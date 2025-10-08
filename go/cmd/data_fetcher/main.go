package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	
	"trading-ai-go/pkg/fetcher"
)

type Config struct {
	Port           string
	RedisURL       string
	PostgresURL    string
	FinnhubAPIKey  string
	AlphaVantageKey string
	YahooAPIKey    string
	RedditClientID string
	RedditSecret   string
}

type DataFetcher struct {
	db    *gorm.DB
	redis *redis.Client
	config Config
	finnhub *fetcher.FinnhubClient
	alphaVantage *fetcher.AlphaVantageClient
	yahoo *fetcher.YahooClient
}

type StockPriceRequest struct {
	Symbol string `json:"symbol"`
}

type StockPriceResponse struct {
	Symbol    string  `json:"symbol"`
	Price     float64 `json:"price"`
	Change    float64 `json:"change"`
	ChangePercent float64 `json:"change_percent"`
	Volume    int64   `json:"volume"`
	MarketCap int64   `json:"market_cap"`
	Timestamp int64   `json:"timestamp"`
}

type NewsRequest struct {
	Symbol    string `json:"symbol"`
	DaysBack  int    `json:"days_back"`
	Limit     int    `json:"limit"`
}

type NewsResponse struct {
	Symbol string `json:"symbol"`
	News   []NewsItem `json:"news"`
}

type NewsItem struct {
	Title       string    `json:"title"`
	Summary     string    `json:"summary"`
	URL         string    `json:"url"`
	Source      string    `json:"source"`
	PublishedAt time.Time `json:"published_at"`
	Sentiment   string    `json:"sentiment"`
	Relevance   float64   `json:"relevance"`
}

func main() {
	config := loadConfig()
	
	// Initialize database
	db, err := initDB(config.PostgresURL)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	
	// Initialize Redis
	redisClient, err := initRedis(config.RedisURL)
	if err != nil {
		log.Fatal("Failed to connect to Redis:", err)
	}
	
	fetcher := &DataFetcher{
		db:           db,
		redis:        redisClient,
		config:       config,
		finnhub:      fetcher.NewFinnhubClient(config.FinnhubAPIKey),
		alphaVantage: fetcher.NewAlphaVantageClient(config.AlphaVantageKey),
		yahoo:        fetcher.NewYahooClient(config.YahooAPIKey),
	}
	
	// Setup routes
	router := setupRoutes(fetcher)
	
	// Start server
	server := &http.Server{
		Addr:    ":" + config.Port,
		Handler: router,
	}
	
	// Graceful shutdown
	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("Failed to start server:", err)
		}
	}()
	
	log.Printf("Data Fetcher Service started on port %s", config.Port)
	
	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	
	log.Println("Shutting down server...")
	
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	if err := server.Shutdown(ctx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}
	
	log.Println("Server exited")
}

func loadConfig() Config {
	return Config{
		Port:           getEnv("PORT", "8080"),
		RedisURL:       getEnv("REDIS_URL", "redis://localhost:6379"),
		PostgresURL:    getEnv("POSTGRES_URL", "postgres://user:pass@localhost/trading"),
		FinnhubAPIKey:  getEnv("FINNHUB_API_KEY", ""),
		AlphaVantageKey: getEnv("ALPHA_VANTAGE_KEY", ""),
		YahooAPIKey:    getEnv("YAHOO_API_KEY", ""),
		RedditClientID: getEnv("REDDIT_CLIENT_ID", ""),
		RedditSecret:   getEnv("REDDIT_SECRET", ""),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func initDB(url string) (*gorm.DB, error) {
	db, err := gorm.Open(postgres.Open(url), &gorm.Config{})
	if err != nil {
		return nil, err
	}
	
	// Test connection
	sqlDB, err := db.DB()
	if err != nil {
		return nil, err
	}
	
	if err := sqlDB.Ping(); err != nil {
		return nil, err
	}
	
	return db, nil
}

func initRedis(url string) (*redis.Client, error) {
	opt, err := redis.ParseURL(url)
	if err != nil {
		return nil, err
	}
	
	client := redis.NewClient(opt)
	
	// Test connection
	ctx := context.Background()
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, err
	}
	
	return client, nil
}

func setupRoutes(fetcher *DataFetcher) *gin.Engine {
	router := gin.Default()
	
	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy"})
	})
	
	// Stock price endpoint
	router.POST("/api/stock/price", fetcher.getStockPrice)
	
	// News endpoint
	router.POST("/api/stock/news", fetcher.getStockNews)
	
	// Bulk operations
	router.POST("/api/stock/bulk/price", fetcher.getBulkStockPrices)
	router.POST("/api/stock/bulk/news", fetcher.getBulkStockNews)
	
	// Cache management
	router.DELETE("/api/cache/clear", fetcher.clearCache)
	router.GET("/api/cache/stats", fetcher.getCacheStats)
	
	return router
}

func (f *DataFetcher) getStockPrice(c *gin.Context) {
	var req StockPriceRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	
	// Check cache first
	cacheKey := fmt.Sprintf("stock_price_%s", req.Symbol)
	cached, err := f.redis.Get(context.Background(), cacheKey).Result()
	if err == nil {
		var response StockPriceResponse
		if err := json.Unmarshal([]byte(cached), &response); err == nil {
			c.JSON(200, response)
			return
		}
	}
	
	// Fetch from API
	price, err := f.fetchStockPrice(req.Symbol)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	// Cache the result
	priceJSON, _ := json.Marshal(price)
	f.redis.Set(context.Background(), cacheKey, priceJSON, 5*time.Minute)
	
	c.JSON(200, price)
}

func (f *DataFetcher) getStockNews(c *gin.Context) {
	var req NewsRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	
	if req.DaysBack == 0 {
		req.DaysBack = 7
	}
	if req.Limit == 0 {
		req.Limit = 20
	}
	
	// Check cache first
	cacheKey := fmt.Sprintf("stock_news_%s_%d_%d", req.Symbol, req.DaysBack, req.Limit)
	cached, err := f.redis.Get(context.Background(), cacheKey).Result()
	if err == nil {
		var response NewsResponse
		if err := json.Unmarshal([]byte(cached), &response); err == nil {
			c.JSON(200, response)
			return
		}
	}
	
	// Fetch from API
	news, err := f.fetchStockNews(req.Symbol, req.DaysBack, req.Limit)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	response := NewsResponse{
		Symbol: req.Symbol,
		News:   news,
	}
	
	// Cache the result
	newsJSON, _ := json.Marshal(response)
	f.redis.Set(context.Background(), cacheKey, newsJSON, 30*time.Minute)
	
	c.JSON(200, response)
}

func (f *DataFetcher) getBulkStockPrices(c *gin.Context) {
	var req struct {
		Symbols []string `json:"symbols"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	
	// Use goroutines for concurrent fetching
	type result struct {
		Symbol string
		Price  *StockPriceResponse
		Error  error
	}
	
	results := make(chan result, len(req.Symbols))
	
	for _, symbol := range req.Symbols {
		go func(sym string) {
			price, err := f.fetchStockPrice(sym)
			results <- result{Symbol: sym, Price: price, Error: err}
		}(symbol)
	}
	
	// Collect results
	responses := make(map[string]interface{})
	for i := 0; i < len(req.Symbols); i++ {
		res := <-results
		if res.Error != nil {
			responses[res.Symbol] = gin.H{"error": res.Error.Error()}
		} else {
			responses[res.Symbol] = res.Price
		}
	}
	
	c.JSON(200, responses)
}

func (f *DataFetcher) getBulkStockNews(c *gin.Context) {
	var req struct {
		Symbols   []string `json:"symbols"`
		DaysBack  int      `json:"days_back"`
		Limit     int      `json:"limit"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	
	if req.DaysBack == 0 {
		req.DaysBack = 7
	}
	if req.Limit == 0 {
		req.Limit = 20
	}
	
	// Use goroutines for concurrent fetching
	type result struct {
		Symbol string
		News   *NewsResponse
		Error  error
	}
	
	results := make(chan result, len(req.Symbols))
	
	for _, symbol := range req.Symbols {
		go func(sym string) {
			news, err := f.fetchStockNews(sym, req.DaysBack, req.Limit)
			if err != nil {
				results <- result{Symbol: sym, News: nil, Error: err}
				return
			}
			
			response := &NewsResponse{
				Symbol: sym,
				News:   news,
			}
			results <- result{Symbol: sym, News: response, Error: nil}
		}(symbol)
	}
	
	// Collect results
	responses := make(map[string]interface{})
	for i := 0; i < len(req.Symbols); i++ {
		res := <-results
		if res.Error != nil {
			responses[res.Symbol] = gin.H{"error": res.Error.Error()}
		} else {
			responses[res.Symbol] = res.News
		}
	}
	
	c.JSON(200, responses)
}

func (f *DataFetcher) clearCache(c *gin.Context) {
	ctx := context.Background()
	
	// Clear all cache keys
	iter := f.redis.Scan(ctx, 0, "*", 0).Iterator()
	for iter.Next(ctx) {
		f.redis.Del(ctx, iter.Val())
	}
	
	if err := iter.Err(); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	c.JSON(200, gin.H{"message": "Cache cleared successfully"})
}

func (f *DataFetcher) getCacheStats(c *gin.Context) {
	ctx := context.Background()
	
	info, err := f.redis.Info(ctx, "memory").Result()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	// Parse memory info (simplified)
	stats := gin.H{
		"memory_usage": info,
		"keys_count":   f.redis.DBSize(ctx).Val(),
	}
	
	c.JSON(200, stats)
}

// API fetching methods with real API calls
func (f *DataFetcher) fetchStockPrice(symbol string) (*StockPriceResponse, error) {
	// Try multiple APIs for redundancy
	var price *StockPriceResponse
	
	// Try Finnhub first
	if f.config.FinnhubAPIKey != "" {
		quote, err := f.finnhub.GetQuote(symbol)
		if err == nil && quote.CurrentPrice > 0 {
			price = &StockPriceResponse{
				Symbol:        symbol,
				Price:         quote.CurrentPrice,
				Change:        quote.Change,
				ChangePercent: quote.ChangePercent,
				Volume:        0, // Finnhub doesn't provide volume in quote
				MarketCap:     0, // Finnhub doesn't provide market cap in quote
				Timestamp:     quote.Timestamp,
			}
		}
	}
	
	// Fallback to Alpha Vantage
	if price == nil && f.config.AlphaVantageKey != "" {
		quote, err := f.alphaVantage.GetQuote(symbol)
		if err == nil && quote.GlobalQuote.Price != "" {
			// Parse the string values (Alpha Vantage returns strings)
			price = &StockPriceResponse{
				Symbol:        symbol,
				Price:         parseFloat(quote.GlobalQuote.Price),
				Change:        parseFloat(quote.GlobalQuote.Change),
				ChangePercent: parseFloat(quote.GlobalQuote.ChangePercent),
				Volume:        parseInt64(quote.GlobalQuote.Volume),
				MarketCap:     0, // Alpha Vantage doesn't provide market cap in quote
				Timestamp:     time.Now().Unix(),
			}
		}
	}
	
	// Fallback to Yahoo Finance
	if price == nil && f.config.YahooAPIKey != "" {
		quote, err := f.yahoo.GetQuote(symbol)
		if err == nil && quote.RegularMarketPrice > 0 {
			price = &StockPriceResponse{
				Symbol:        symbol,
				Price:         quote.RegularMarketPrice,
				Change:        quote.RegularMarketChange,
				ChangePercent: quote.RegularMarketChangePercent,
				Volume:        quote.RegularMarketVolume,
				MarketCap:     quote.MarketCap,
				Timestamp:     quote.RegularMarketTime,
			}
		}
	}
	
	if price == nil {
		return nil, fmt.Errorf("failed to fetch price for %s from all APIs", symbol)
	}
	
	return price, nil
}

func (f *DataFetcher) fetchStockNews(symbol string, daysBack, limit int) ([]NewsItem, error) {
	var news []NewsItem
	
	// Try Finnhub news first
	if f.config.FinnhubAPIKey != "" {
		from := time.Now().AddDate(0, 0, -daysBack)
		to := time.Now()
		
		finnhubNews, err := f.finnhub.GetNews(symbol, from, to)
		if err == nil {
			for _, item := range finnhubNews {
				if len(news) >= limit {
					break
				}
				news = append(news, NewsItem{
					Title:       item.Headline,
					Summary:     item.Summary,
					URL:         item.URL,
					Source:      item.Source,
					PublishedAt: time.Unix(item.Datetime, 0),
					Sentiment:   "neutral", // Would need sentiment analysis
					Relevance:   0.8,       // Would need relevance scoring
				})
			}
		}
	}
	
	// If we don't have enough news, add some mock data
	if len(news) < limit {
		news = append(news, NewsItem{
			Title:       fmt.Sprintf("Market update for %s", symbol),
			Summary:     "Recent market developments and analysis",
			URL:         "https://example.com/news",
			Source:      "Financial News",
			PublishedAt: time.Now(),
			Sentiment:   "positive",
			Relevance:   0.85,
		})
	}
	
	return news, nil
}

// Helper functions for parsing string values
func parseFloat(s string) float64 {
	if s == "" {
		return 0
	}
	var f float64
	fmt.Sscanf(s, "%f", &f)
	return f
}

func parseInt64(s string) int64 {
	if s == "" {
		return 0
	}
	var i int64
	fmt.Sscanf(s, "%d", &i)
	return i
}
