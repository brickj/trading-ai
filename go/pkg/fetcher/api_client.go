package fetcher

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type APIClient struct {
	httpClient *http.Client
	rateLimiter *RateLimiter
}

type RateLimiter struct {
	requests chan struct{}
	ticker   *time.Ticker
}

func NewAPIClient() *APIClient {
	return &APIClient{
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		rateLimiter: NewRateLimiter(100, time.Minute), // 100 requests per minute
	}
}

func NewRateLimiter(requests int, duration time.Duration) *RateLimiter {
	rl := &RateLimiter{
		requests: make(chan struct{}, requests),
		ticker:   time.NewTicker(duration),
	}
	
	// Fill the channel initially
	for i := 0; i < requests; i++ {
		rl.requests <- struct{}{}
	}
	
	// Refill the channel periodically
	go func() {
		for range rl.ticker.C {
			for i := 0; i < requests; i++ {
				select {
				case rl.requests <- struct{}{}:
				default:
					break
				}
			}
		}
	}()
	
	return rl
}

func (rl *RateLimiter) Wait() {
	<-rl.requests
}

func (c *APIClient) Get(url string) (*http.Response, error) {
	c.rateLimiter.Wait()
	return c.httpClient.Get(url)
}

func (c *APIClient) Post(url, contentType string, body io.Reader) (*http.Response, error) {
	c.rateLimiter.Wait()
	return c.httpClient.Post(url, contentType, body)
}

// Finnhub API client
type FinnhubClient struct {
	*APIClient
	apiKey string
	baseURL string
}

func NewFinnhubClient(apiKey string) *FinnhubClient {
	return &FinnhubClient{
		APIClient: NewAPIClient(),
		apiKey:    apiKey,
		baseURL:   "https://finnhub.io/api/v1",
	}
}

type FinnhubQuote struct {
	CurrentPrice  float64 `json:"c"`
	Change        float64 `json:"d"`
	ChangePercent float64 `json:"dp"`
	High          float64 `json:"h"`
	Low           float64 `json:"l"`
	Open          float64 `json:"o"`
	PreviousClose float64 `json:"pc"`
	Timestamp     int64   `json:"t"`
}

type FinnhubNews struct {
	Category string `json:"category"`
	Datetime int64  `json:"datetime"`
	Headline string `json:"headline"`
	ID       int    `json:"id"`
	Image    string `json:"image"`
	Related  string `json:"related"`
	Source   string `json:"source"`
	Summary  string `json:"summary"`
	URL      string `json:"url"`
}

func (f *FinnhubClient) GetQuote(symbol string) (*FinnhubQuote, error) {
	url := fmt.Sprintf("%s/quote?symbol=%s&token=%s", f.baseURL, symbol, f.apiKey)
	
	resp, err := f.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed with status: %d", resp.StatusCode)
	}
	
	var quote FinnhubQuote
	if err := json.NewDecoder(resp.Body).Decode(&quote); err != nil {
		return nil, err
	}
	
	return &quote, nil
}

func (f *FinnhubClient) GetNews(symbol string, from, to time.Time) ([]FinnhubNews, error) {
	url := fmt.Sprintf("%s/company-news?symbol=%s&from=%d&to=%d&token=%s", 
		f.baseURL, symbol, from.Unix(), to.Unix(), f.apiKey)
	
	resp, err := f.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed with status: %d", resp.StatusCode)
	}
	
	var news []FinnhubNews
	if err := json.NewDecoder(resp.Body).Decode(&news); err != nil {
		return nil, err
	}
	
	return news, nil
}

// Alpha Vantage API client
type AlphaVantageClient struct {
	*APIClient
	apiKey string
	baseURL string
}

func NewAlphaVantageClient(apiKey string) *AlphaVantageClient {
	return &AlphaVantageClient{
		APIClient: NewAPIClient(),
		apiKey:    apiKey,
		baseURL:   "https://www.alphavantage.co/query",
	}
}

type AlphaVantageQuote struct {
	GlobalQuote struct {
		Symbol           string `json:"01. symbol"`
		Open             string `json:"02. open"`
		High             string `json:"03. high"`
		Low              string `json:"04. low"`
		Price            string `json:"05. price"`
		Volume           string `json:"06. volume"`
		LatestTradingDay string `json:"07. latest trading day"`
		PreviousClose    string `json:"08. previous close"`
		Change           string `json:"09. change"`
		ChangePercent    string `json:"10. change percent"`
	} `json:"Global Quote"`
}

func (a *AlphaVantageClient) GetQuote(symbol string) (*AlphaVantageQuote, error) {
	url := fmt.Sprintf("%s?function=GLOBAL_QUOTE&symbol=%s&apikey=%s", 
		a.baseURL, symbol, a.apiKey)
	
	resp, err := a.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed with status: %d", resp.StatusCode)
	}
	
	var quote AlphaVantageQuote
	if err := json.NewDecoder(resp.Body).Decode(&quote); err != nil {
		return nil, err
	}
	
	return &quote, nil
}

// Yahoo Finance API client (using RapidAPI)
type YahooClient struct {
	*APIClient
	apiKey string
	baseURL string
}

func NewYahooClient(apiKey string) *YahooClient {
	return &YahooClient{
		APIClient: NewAPIClient(),
		apiKey:    apiKey,
		baseURL:   "https://yahoo-finance15.p.rapidapi.com/api/v1",
	}
}

type YahooQuote struct {
	Symbol             string  `json:"symbol"`
	ShortName          string  `json:"shortName"`
	LongName           string  `json:"longName"`
	RegularMarketPrice float64 `json:"regularMarketPrice"`
	RegularMarketChange float64 `json:"regularMarketChange"`
	RegularMarketChangePercent float64 `json:"regularMarketChangePercent"`
	RegularMarketVolume int64   `json:"regularMarketVolume"`
	MarketCap          int64   `json:"marketCap"`
	RegularMarketTime  int64   `json:"regularMarketTime"`
}

func (y *YahooClient) GetQuote(symbol string) (*YahooQuote, error) {
	url := fmt.Sprintf("%s/markets/quote?ticker=%s", y.baseURL, symbol)
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("X-RapidAPI-Key", y.apiKey)
	req.Header.Set("X-RapidAPI-Host", "yahoo-finance15.p.rapidapi.com")
	
	resp, err := y.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed with status: %d", resp.StatusCode)
	}
	
	var quote YahooQuote
	if err := json.NewDecoder(resp.Body).Decode(&quote); err != nil {
		return nil, err
	}
	
	return &quote, nil
}
