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
)

type Config struct {
	Port     string
	RedisURL string
}

type CacheService struct {
	redis  *redis.Client
	config Config
}

type CacheRequest struct {
	Key   string      `json:"key"`
	Value interface{} `json:"value"`
	TTL   int         `json:"ttl"` // TTL in seconds
}

type CacheResponse struct {
	Key   string      `json:"key"`
	Value interface{} `json:"value"`
	Found bool        `json:"found"`
}

type BulkCacheRequest struct {
	Keys []string `json:"keys"`
}

type BulkCacheResponse struct {
	Results map[string]interface{} `json:"results"`
}

type CacheStats struct {
	MemoryUsage    string `json:"memory_usage"`
	KeysCount      int64  `json:"keys_count"`
	HitRate        float64 `json:"hit_rate"`
	MissRate       float64 `json:"miss_rate"`
	TotalCommands  int64  `json:"total_commands"`
	ConnectedClients int64 `json:"connected_clients"`
}

func main() {
	config := loadConfig()
	
	// Initialize Redis
	redisClient, err := initRedis(config.RedisURL)
	if err != nil {
		log.Fatal("Failed to connect to Redis:", err)
	}
	
	service := &CacheService{
		redis:  redisClient,
		config: config,
	}
	
	// Setup routes
	router := setupRoutes(service)
	
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
	
	log.Printf("Cache Service started on port %s", config.Port)
	
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
		Port:     getEnv("PORT", "8081"),
		RedisURL: getEnv("REDIS_URL", "redis://localhost:6379"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
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

func setupRoutes(service *CacheService) *gin.Engine {
	router := gin.Default()
	
	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy"})
	})
	
	// Cache operations
	router.GET("/api/cache/get/:key", service.get)
	router.POST("/api/cache/set", service.set)
	router.DELETE("/api/cache/delete/:key", service.delete)
	router.POST("/api/cache/bulk/get", service.bulkGet)
	router.POST("/api/cache/bulk/set", service.bulkSet)
	router.DELETE("/api/cache/clear", service.clear)
	router.GET("/api/cache/stats", service.getStats)
	
	// Pattern operations
	router.GET("/api/cache/keys/:pattern", service.getKeys)
	router.DELETE("/api/cache/delete/pattern/:pattern", service.deletePattern)
	
	return router
}

func (s *CacheService) get(c *gin.Context) {
	key := c.Param("key")
	
	ctx := context.Background()
	value, err := s.redis.Get(ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			c.JSON(200, CacheResponse{
				Key:   key,
				Value: nil,
				Found: false,
			})
			return
		}
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	// Try to parse as JSON
	var jsonValue interface{}
	if err := json.Unmarshal([]byte(value), &jsonValue); err != nil {
		// If not JSON, return as string
		jsonValue = value
	}
	
	c.JSON(200, CacheResponse{
		Key:   key,
		Value: jsonValue,
		Found: true,
	})
}

func (s *CacheService) set(c *gin.Context) {
	var req CacheRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	
	ctx := context.Background()
	
	// Convert value to JSON
	valueBytes, err := json.Marshal(req.Value)
	if err != nil {
		c.JSON(400, gin.H{"error": "Failed to marshal value to JSON"})
		return
	}
	
	// Set with TTL
	ttl := time.Duration(req.TTL) * time.Second
	if ttl == 0 {
		ttl = time.Hour // Default TTL
	}
	
	err = s.redis.Set(ctx, req.Key, valueBytes, ttl).Err()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	c.JSON(200, gin.H{"message": "Cache set successfully"})
}

func (s *CacheService) delete(c *gin.Context) {
	key := c.Param("key")
	
	ctx := context.Background()
	err := s.redis.Del(ctx, key).Err()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	c.JSON(200, gin.H{"message": "Cache deleted successfully"})
}

func (s *CacheService) bulkGet(c *gin.Context) {
	var req BulkCacheRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	
	ctx := context.Background()
	results := make(map[string]interface{})
	
	// Use pipeline for better performance
	pipe := s.redis.Pipeline()
	cmds := make(map[string]*redis.StringCmd)
	
	for _, key := range req.Keys {
		cmds[key] = pipe.Get(ctx, key)
	}
	
	_, err := pipe.Exec(ctx)
	if err != nil && err != redis.Nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	// Process results
	for key, cmd := range cmds {
		value, err := cmd.Result()
		if err != nil {
			if err == redis.Nil {
				results[key] = nil
			} else {
				results[key] = gin.H{"error": err.Error()}
			}
		} else {
			// Try to parse as JSON
			var jsonValue interface{}
			if err := json.Unmarshal([]byte(value), &jsonValue); err != nil {
				jsonValue = value
			}
			results[key] = jsonValue
		}
	}
	
	c.JSON(200, BulkCacheResponse{Results: results})
}

func (s *CacheService) bulkSet(c *gin.Context) {
	var req map[string]CacheRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	
	ctx := context.Background()
	
	// Use pipeline for better performance
	pipe := s.redis.Pipeline()
	
	for key, cacheReq := range req {
		valueBytes, err := json.Marshal(cacheReq.Value)
		if err != nil {
			c.JSON(400, gin.H{"error": fmt.Sprintf("Failed to marshal value for key %s", key)})
			return
		}
		
		ttl := time.Duration(cacheReq.TTL) * time.Second
		if ttl == 0 {
			ttl = time.Hour // Default TTL
		}
		
		pipe.Set(ctx, key, valueBytes, ttl)
	}
	
	_, err := pipe.Exec(ctx)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	c.JSON(200, gin.H{"message": "Bulk cache set successfully"})
}

func (s *CacheService) clear(c *gin.Context) {
	ctx := context.Background()
	
	// Clear all cache keys
	iter := s.redis.Scan(ctx, 0, "*", 0).Iterator()
	for iter.Next(ctx) {
		s.redis.Del(ctx, iter.Val())
	}
	
	if err := iter.Err(); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	c.JSON(200, gin.H{"message": "Cache cleared successfully"})
}

func (s *CacheService) getStats(c *gin.Context) {
	ctx := context.Background()
	
	// Get Redis info
	info, err := s.redis.Info(ctx, "memory", "stats").Result()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	// Parse info (simplified)
	stats := CacheStats{
		MemoryUsage:    info,
		KeysCount:      s.redis.DBSize(ctx).Val(),
		HitRate:        0.0, // Would need to calculate from stats
		MissRate:       0.0, // Would need to calculate from stats
		TotalCommands:  0,   // Would need to parse from info
		ConnectedClients: 0, // Would need to parse from info
	}
	
	c.JSON(200, stats)
}

func (s *CacheService) getKeys(c *gin.Context) {
	pattern := c.Param("pattern")
	if pattern == "" {
		pattern = "*"
	}
	
	ctx := context.Background()
	keys, err := s.redis.Keys(ctx, pattern).Result()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	c.JSON(200, gin.H{"keys": keys})
}

func (s *CacheService) deletePattern(c *gin.Context) {
	pattern := c.Param("pattern")
	if pattern == "" {
		c.JSON(400, gin.H{"error": "Pattern is required"})
		return
	}
	
	ctx := context.Background()
	
	// Get keys matching pattern
	keys, err := s.redis.Keys(ctx, pattern).Result()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	
	// Delete keys
	if len(keys) > 0 {
		err = s.redis.Del(ctx, keys...).Err()
		if err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}
	}
	
	c.JSON(200, gin.H{
		"message": fmt.Sprintf("Deleted %d keys matching pattern %s", len(keys), pattern),
		"deleted_count": len(keys),
	})
}
