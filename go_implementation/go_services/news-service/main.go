package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/mux"
)

// NewsRequest represents a request for news data
type NewsRequest struct {
	Symbols      []string `json:"symbols"`
	HoursBack    int      `json:"hours_back"`
	Categories   []string `json:"categories"`
	MinArticles  int      `json:"min_articles"`
}

// TrendingRequest represents a request for trending news
type TrendingRequest struct {
	HoursBack       int      `json:"hours_back"`
	WatchlistStocks []string `json:"watchlist_stocks"`
	WatchlistCrypto []string `json:"watchlist_crypto"`
	Categories      []string `json:"categories"`
}

// NewsArticle represents a news article
type NewsArticle struct {
	ID       string    `json:"id"`
	Headline string    `json:"headline"`
	Summary  string    `json:"summary"`
	Source   string    `json:"source"`
	DateTime time.Time `json:"datetime"`
	URL      string    `json:"url"`
	Symbols  []string  `json:"symbols"`
}

// NewsResponse represents the response from news fetch
type NewsResponse struct {
	Success      bool                    `json:"success"`
	ArticleCount int                     `json:"article_count"`
	ProcessTime  float64                 `json:"process_time_ms"`
	Data         map[string][]NewsArticle `json:"data"`
}

// TrendingResponse represents the response from trending news
type TrendingResponse struct {
	Success         bool                    `json:"success"`
	SymbolCount     int                     `json:"symbol_count"`
	ProcessTime     float64                 `json:"process_time_ms"`
	TrendingSymbols map[string][]NewsArticle `json:"trending_symbols"`
}

// HealthResponse represents service health status
type HealthResponse struct {
	Status    string    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
	Version   string    `json:"version"`
	Uptime    string    `json:"uptime"`
}

// ServiceStats represents service statistics
type ServiceStats struct {
	RequestsProcessed int64   `json:"requests_processed"`
	ArticlesProcessed int64   `json:"articles_processed"`
	AverageLatency    float64 `json:"average_latency_ms"`
	ErrorRate         float64 `json:"error_rate"`
	Uptime            string  `json:"uptime"`
}

var (
	startTime         = time.Now()
	requestsProcessed int64
	articlesProcessed int64
	totalLatency      float64
	errorCount        int64
	statsMutex        sync.RWMutex
)

func main() {
	port := getEnv("NEWS_SERVICE_PORT", "8081")
	
	r := mux.NewRouter()
	
	// Health check endpoint
	r.HandleFunc("/health", healthHandler).Methods("GET")
	
	// News API endpoints
	r.HandleFunc("/api/v1/news/fetch", fetchNewsHandler).Methods("POST")
	r.HandleFunc("/api/v1/news/trending", trendingNewsHandler).Methods("POST")
	r.HandleFunc("/api/v1/news/stats", statsHandler).Methods("GET")
	
	// CORS middleware
	r.Use(corsMiddleware)
	
	log.Printf("🚀 News Service starting on port %s", port)
	log.Printf("📊 Endpoints available:")
	log.Printf("   GET  /health - Health check")
	log.Printf("   POST /api/v1/news/fetch - Fetch news for symbols")
	log.Printf("   POST /api/v1/news/trending - Process trending news")
	log.Printf("   GET  /api/v1/news/stats - Service statistics")
	
	log.Fatal(http.ListenAndServe(":"+port, r))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	response := HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now(),
		Version:   "1.0.0",
		Uptime:    time.Since(startTime).String(),
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func fetchNewsHandler(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()
	
	var req NewsRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		incrementErrorCount()
		return
	}
	
	// Simulate high-performance news fetching
	newsData := make(map[string][]NewsArticle)
	totalArticles := 0
	
	// Process symbols concurrently for better performance
	var wg sync.WaitGroup
	var mu sync.Mutex
	
	for _, symbol := range req.Symbols {
		wg.Add(1)
		go func(sym string) {
			defer wg.Done()
			
			// Simulate fetching news for symbol
			articles := simulateNewsFetch(sym, req.HoursBack, req.Categories)
			
			mu.Lock()
			newsData[sym] = articles
			totalArticles += len(articles)
			mu.Unlock()
		}(symbol)
	}
	
	wg.Wait()
	
	processTime := float64(time.Since(startTime).Nanoseconds()) / 1e6
	
	response := NewsResponse{
		Success:      true,
		ArticleCount: totalArticles,
		ProcessTime:  processTime,
		Data:         newsData,
	}
	
	// Update statistics
	updateStats(processTime, int64(totalArticles))
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
	
	log.Printf("📰 Processed %d symbols, found %d articles in %.2fms", 
		len(req.Symbols), totalArticles, processTime)
}

func trendingNewsHandler(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()
	
	var req TrendingRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		incrementErrorCount()
		return
	}
	
	// Simulate trending news analysis
	trendingSymbols := make(map[string][]NewsArticle)
	
	// Combine watchlist symbols
	allSymbols := append(req.WatchlistStocks, req.WatchlistCrypto...)
	
	// Process trending analysis concurrently
	var wg sync.WaitGroup
	var mu sync.Mutex
	
	for _, symbol := range allSymbols {
		wg.Add(1)
		go func(sym string) {
			defer wg.Done()
			
			// Simulate trending analysis
			articles := simulateTrendingAnalysis(sym, req.HoursBack)
			
			// Only include symbols with significant news activity
			if len(articles) >= 3 {
				mu.Lock()
				trendingSymbols[sym] = articles
				mu.Unlock()
			}
		}(symbol)
	}
	
	wg.Wait()
	
	processTime := float64(time.Since(startTime).Nanoseconds()) / 1e6
	
	response := TrendingResponse{
		Success:         true,
		SymbolCount:     len(trendingSymbols),
		ProcessTime:     processTime,
		TrendingSymbols: trendingSymbols,
	}
	
	// Update statistics
	totalArticles := 0
	for _, articles := range trendingSymbols {
		totalArticles += len(articles)
	}
	updateStats(processTime, int64(totalArticles))
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
	
	log.Printf("📈 Found %d trending symbols with %d total articles in %.2fms", 
		len(trendingSymbols), totalArticles, processTime)
}

func statsHandler(w http.ResponseWriter, r *http.Request) {
	statsMutex.RLock()
	defer statsMutex.RUnlock()
	
	var avgLatency float64
	if requestsProcessed > 0 {
		avgLatency = totalLatency / float64(requestsProcessed)
	}
	
	var errorRate float64
	if requestsProcessed > 0 {
		errorRate = float64(errorCount) / float64(requestsProcessed) * 100
	}
	
	stats := ServiceStats{
		RequestsProcessed: requestsProcessed,
		ArticlesProcessed: articlesProcessed,
		AverageLatency:    avgLatency,
		ErrorRate:         errorRate,
		Uptime:            time.Since(startTime).String(),
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func simulateNewsFetch(symbol string, hoursBack int, categories []string) []NewsArticle {
	// Simulate realistic news fetching with some randomness
	articleCount := 2 + (len(symbol) % 8) // 2-9 articles per symbol
	articles := make([]NewsArticle, articleCount)
	
	for i := 0; i < articleCount; i++ {
		articles[i] = NewsArticle{
			ID:       fmt.Sprintf("%s_%d_%d", symbol, time.Now().Unix(), i),
			Headline: fmt.Sprintf("Breaking: %s shows significant market movement", symbol),
			Summary:  fmt.Sprintf("Latest analysis of %s indicates potential trading opportunities based on recent market data and sentiment analysis.", symbol),
			Source:   "Financial News API",
			DateTime: time.Now().Add(-time.Duration(i) * time.Hour),
			URL:      fmt.Sprintf("https://example.com/news/%s_%d", symbol, i),
			Symbols:  []string{symbol},
		}
	}
	
	// Simulate processing delay (much faster than Python)
	time.Sleep(time.Millisecond * 5) // 5ms vs Python's ~50ms
	
	return articles
}

func simulateTrendingAnalysis(symbol string, hoursBack int) []NewsArticle {
	// Simulate trending analysis - some symbols have more activity
	activityLevel := (len(symbol) + int(time.Now().Unix())) % 10
	
	if activityLevel < 3 {
		return []NewsArticle{} // Low activity
	}
	
	articleCount := activityLevel // 3-9 articles for trending symbols
	articles := make([]NewsArticle, articleCount)
	
	for i := 0; i < articleCount; i++ {
		articles[i] = NewsArticle{
			ID:       fmt.Sprintf("trending_%s_%d_%d", symbol, time.Now().Unix(), i),
			Headline: fmt.Sprintf("TRENDING: %s gains attention in financial markets", symbol),
			Summary:  fmt.Sprintf("Market analysts are closely watching %s as it shows increased trading volume and social media mentions.", symbol),
			Source:   "Market Trends API",
			DateTime: time.Now().Add(-time.Duration(i*30) * time.Minute),
			URL:      fmt.Sprintf("https://example.com/trending/%s_%d", symbol, i),
			Symbols:  []string{symbol},
		}
	}
	
	// Simulate processing delay
	time.Sleep(time.Millisecond * 3) // Very fast processing
	
	return articles
}

func updateStats(latency float64, articles int64) {
	statsMutex.Lock()
	defer statsMutex.Unlock()
	
	requestsProcessed++
	articlesProcessed += articles
	totalLatency += latency
}

func incrementErrorCount() {
	statsMutex.Lock()
	defer statsMutex.Unlock()
	
	errorCount++
	requestsProcessed++
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
} 