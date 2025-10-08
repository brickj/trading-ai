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
)

type Config struct {
	Port        string
	RedisURL    string
	PostgresURL string
	WorkerCount int
}

type BackgroundWorker struct {
	db     *gorm.DB
	redis  *redis.Client
	config Config
	ctx    context.Context
	cancel context.CancelFunc
}

type JobRequest struct {
	Type      string                 `json:"type"`
	Data      map[string]interface{} `json:"data"`
	Priority  int                    `json:"priority"`
	Delay     int                    `json:"delay"` // Delay in seconds
}

type JobResponse struct {
	ID        string                 `json:"id"`
	Type      string                 `json:"type"`
	Status    string                 `json:"status"`
	Result    map[string]interface{} `json:"result,omitempty"`
	Error     string                 `json:"error,omitempty"`
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
}

type WorkerStats struct {
	ActiveWorkers   int                    `json:"active_workers"`
	ProcessedJobs   int64                  `json:"processed_jobs"`
	FailedJobs      int64                  `json:"failed_jobs"`
	QueuedJobs      int64                  `json:"queued_jobs"`
	WorkerStatus    map[string]interface{} `json:"worker_status"`
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
	
	ctx, cancel := context.WithCancel(context.Background())
	
	worker := &BackgroundWorker{
		db:     db,
		redis:  redisClient,
		config: config,
		ctx:    ctx,
		cancel: cancel,
	}
	
	// Start background workers
	worker.startWorkers()
	
	// Setup routes
	router := setupRoutes(worker)
	
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
	
	log.Printf("Background Workers started on port %s with %d workers", config.Port, config.WorkerCount)
	
	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	
	log.Println("Shutting down workers...")
	cancel()
	
	log.Println("Shutting down server...")
	
	ctx, cancel = context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	if err := server.Shutdown(ctx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}
	
	log.Println("Server exited")
}

func loadConfig() Config {
	return Config{
		Port:        getEnv("PORT", "8082"),
		RedisURL:    getEnv("REDIS_URL", "redis://localhost:6379"),
		PostgresURL: getEnv("POSTGRES_URL", "postgres://user:pass@localhost/trading"),
		WorkerCount: getEnvInt("WORKER_COUNT", 5),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		var i int
		if _, err := fmt.Sscanf(value, "%d", &i); err == nil {
			return i
		}
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

func (w *BackgroundWorker) startWorkers() {
	for i := 0; i < w.config.WorkerCount; i++ {
		go w.worker(i)
	}
}

func (w *BackgroundWorker) worker(workerID int) {
	log.Printf("Worker %d started", workerID)
	
	for {
		select {
		case <-w.ctx.Done():
			log.Printf("Worker %d shutting down", workerID)
			return
		default:
			// Process jobs from Redis queue
			w.processJob(workerID)
			time.Sleep(100 * time.Millisecond) // Small delay to prevent busy waiting
		}
	}
}

func (w *BackgroundWorker) processJob(workerID int) {
	ctx := context.Background()
	
	// Get job from queue (using Redis list as queue)
	jobData, err := w.redis.BRPop(ctx, 5*time.Second, "job_queue").Result()
	if err != nil {
		if err != redis.Nil {
			log.Printf("Worker %d error getting job: %v", workerID, err)
		}
		return
	}
	
	if len(jobData) < 2 {
		return
	}
	
	// Parse job
	var job JobRequest
	if err := json.Unmarshal([]byte(jobData[1]), &job); err != nil {
		log.Printf("Worker %d error parsing job: %v", workerID, err)
		return
	}
	
	log.Printf("Worker %d processing job: %s", workerID, job.Type)
	
	// Process job based on type
	result, err := w.executeJob(job)
	
	// Store result
	jobResponse := JobResponse{
		ID:        fmt.Sprintf("job_%d_%d", workerID, time.Now().Unix()),
		Type:      job.Type,
		Status:    "completed",
		Result:    result,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	
	if err != nil {
		jobResponse.Status = "failed"
		jobResponse.Error = err.Error()
		log.Printf("Worker %d job failed: %v", workerID, err)
	}
	
	// Store result in Redis
	resultKey := fmt.Sprintf("job_result_%s", jobResponse.ID)
	resultJSON, _ := json.Marshal(jobResponse)
	w.redis.Set(ctx, resultKey, resultJSON, time.Hour)
	
	log.Printf("Worker %d completed job: %s", workerID, job.Type)
}

func (w *BackgroundWorker) executeJob(job JobRequest) (map[string]interface{}, error) {
	switch job.Type {
	case "update_historical_data":
		return w.updateHistoricalData(job.Data)
	case "preload_stock_data":
		return w.preloadStockData(job.Data)
	case "run_scalping_analysis":
		return w.runScalpingAnalysis(job.Data)
	case "populate_weekly_plan":
		return w.populateWeeklyPlan(job.Data)
	case "preload_news_opportunities":
		return w.preloadNewsOpportunities(job.Data)
	case "sentiment_analysis":
		return w.runSentimentAnalysis(job.Data)
	case "market_analysis":
		return w.runMarketAnalysis(job.Data)
	default:
		return nil, fmt.Errorf("unknown job type: %s", job.Type)
	}
}

func (w *BackgroundWorker) updateHistoricalData(data map[string]interface{}) (map[string]interface{}, error) {
	// Implement historical data update logic
	log.Println("Updating historical data...")
	
	// Simulate work
	time.Sleep(2 * time.Second)
	
	return map[string]interface{}{
		"message": "Historical data updated successfully",
		"updated_symbols": []string{"AAPL", "GOOGL", "MSFT"},
		"records_updated": 1500,
	}, nil
}

func (w *BackgroundWorker) preloadStockData(data map[string]interface{}) (map[string]interface{}, error) {
	// Implement stock data preloading logic
	log.Println("Preloading stock data...")
	
	// Simulate work
	time.Sleep(3 * time.Second)
	
	return map[string]interface{}{
		"message": "Stock data preloaded successfully",
		"preloaded_symbols": []string{"AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"},
		"records_preloaded": 2500,
	}, nil
}

func (w *BackgroundWorker) runScalpingAnalysis(data map[string]interface{}) (map[string]interface{}, error) {
	// Implement scalping analysis logic
	log.Println("Running scalping analysis...")
	
	// Simulate work
	time.Sleep(5 * time.Second)
	
	return map[string]interface{}{
		"message": "Scalping analysis completed successfully",
		"signals_generated": 25,
		"high_probability_signals": 8,
	}, nil
}

func (w *BackgroundWorker) populateWeeklyPlan(data map[string]interface{}) (map[string]interface{}, error) {
	// Implement weekly plan population logic
	log.Println("Populating weekly plan...")
	
	// Simulate work
	time.Sleep(2 * time.Second)
	
	return map[string]interface{}{
		"message": "Weekly plan populated successfully",
		"events_added": 45,
		"earnings_events": 12,
		"economic_events": 8,
	}, nil
}

func (w *BackgroundWorker) preloadNewsOpportunities(data map[string]interface{}) (map[string]interface{}, error) {
	// Implement news opportunities preloading logic
	log.Println("Preloading news opportunities...")
	
	// Simulate work
	time.Sleep(4 * time.Second)
	
	return map[string]interface{}{
		"message": "News opportunities preloaded successfully",
		"opportunities_found": 18,
		"high_impact_news": 5,
	}, nil
}

func (w *BackgroundWorker) runSentimentAnalysis(data map[string]interface{}) (map[string]interface{}, error) {
	// Implement sentiment analysis logic
	log.Println("Running sentiment analysis...")
	
	// Simulate work
	time.Sleep(3 * time.Second)
	
	return map[string]interface{}{
		"message": "Sentiment analysis completed successfully",
		"articles_analyzed": 150,
		"positive_sentiment": 0.65,
		"negative_sentiment": 0.25,
		"neutral_sentiment": 0.10,
	}, nil
}

func (w *BackgroundWorker) runMarketAnalysis(data map[string]interface{}) (map[string]interface{}, error) {
	// Implement market analysis logic
	log.Println("Running market analysis...")
	
	// Simulate work
	time.Sleep(6 * time.Second)
	
	return map[string]interface{}{
		"message": "Market analysis completed successfully",
		"market_trend": "bullish",
		"volatility_index": 0.35,
		"recommendations": 12,
	}, nil
}

func setupRoutes(worker *BackgroundWorker) *gin.Engine {
	router := gin.Default()
	
	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy"})
	})
	
	// Job management
	router.POST("/api/jobs/submit", worker.submitJob)
	router.GET("/api/jobs/status/:id", worker.getJobStatus)
	router.GET("/api/jobs/stats", worker.getStats)
	router.DELETE("/api/jobs/clear", worker.clearJobs)
	
	// Worker management
	router.GET("/api/workers/stats", worker.getWorkerStats)
	router.POST("/api/workers/restart", worker.restartWorkers)
	
	return router
}

func (w *BackgroundWorker) submitJob(c *gin.Context) {
	var req JobRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	
	// Add delay if specified
	if req.Delay > 0 {
		time.Sleep(time.Duration(req.Delay) * time.Second)
	}
	
	// Add job to queue
	jobJSON, err := json.Marshal(req)
	if err != nil {
		c.JSON(500, gin.H{"error": "Failed to marshal job"})
		return
	}
	
	ctx := context.Background()
	err = w.redis.LPush(ctx, "job_queue", jobJSON).Err()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	c.JSON(200, gin.H{"message": "Job submitted successfully"})
}

func (w *BackgroundWorker) getJobStatus(c *gin.Context) {
	jobID := c.Param("id")
	
	ctx := context.Background()
	resultKey := fmt.Sprintf("job_result_%s", jobID)
	
	result, err := w.redis.Get(ctx, resultKey).Result()
	if err != nil {
		if err == redis.Nil {
			c.JSON(404, gin.H{"error": "Job not found"})
			return
		}
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	var jobResponse JobResponse
	if err := json.Unmarshal([]byte(result), &jobResponse); err != nil {
		c.JSON(500, gin.H{"error": "Failed to parse job result"})
		return
	}
	
	c.JSON(200, jobResponse)
}

func (w *BackgroundWorker) getStats(c *gin.Context) {
	ctx := context.Background()
	
	// Get queue length
	queueLength, err := w.redis.LLen(ctx, "job_queue").Result()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	// Get completed jobs count (simplified)
	completedJobs, err := w.redis.Keys(ctx, "job_result_*").Result()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	stats := gin.H{
		"queued_jobs":    queueLength,
		"completed_jobs": len(completedJobs),
		"active_workers": w.config.WorkerCount,
	}
	
	c.JSON(200, stats)
}

func (w *BackgroundWorker) clearJobs(c *gin.Context) {
	ctx := context.Background()
	
	// Clear job queue
	err := w.redis.Del(ctx, "job_queue").Err()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	// Clear job results
	keys, err := w.redis.Keys(ctx, "job_result_*").Result()
	if err == nil && len(keys) > 0 {
		w.redis.Del(ctx, keys...)
	}
	
	c.JSON(200, gin.H{"message": "Jobs cleared successfully"})
}

func (w *BackgroundWorker) getWorkerStats(c *gin.Context) {
	stats := WorkerStats{
		ActiveWorkers: w.config.WorkerCount,
		ProcessedJobs: 0, // Would need to track this
		FailedJobs:    0, // Would need to track this
		QueuedJobs:    0, // Would need to get from Redis
		WorkerStatus: map[string]interface{}{
			"status": "running",
			"uptime": "1h 23m",
		},
	}
	
	c.JSON(200, stats)
}

func (w *BackgroundWorker) restartWorkers(c *gin.Context) {
	// This would restart workers in a real implementation
	c.JSON(200, gin.H{"message": "Workers restart initiated"})
}
