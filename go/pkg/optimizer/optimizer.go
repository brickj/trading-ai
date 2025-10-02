package optimizer

import (
	"fmt"
	"math"
	"strconv"
	"strings"
	"time"
)

type Article struct {
	Weight      float64 `json:"weight"`
	Headline    string  `json:"headline"`
	Summary     string  `json:"summary"`
	Source      string  `json:"source"`
	PublishedAt string  `json:"published_at"`
}

type HistoryPoint struct {
	Sentiment      float64 `json:"sentiment"`
	RealizedReturn float64 `json:"realized_return"`
	Confidence     float64 `json:"confidence"`
	Volume         float64 `json:"volume"`
	Source         string  `json:"source"`
	Timestamp      string  `json:"timestamp"`
}

type Input struct {
	Articles []Article      `json:"articles"`
	History  []HistoryPoint `json:"history"`
}

type Output struct {
	Weights              []float64          `json:"weights"`
	BaselineShift        float64            `json:"baseline_shift"`
	ConfidenceAdjustment float64            `json:"confidence_adjustment"`
	Diagnostics          map[string]float64 `json:"diagnostics"`
	Notes                []string           `json:"notes"`
}

type sourceAggregate struct {
	Accuracy float64
	Weight   float64
	Count    int
	Original string
}

// Optimize returns re-weighted news articles and historical adjustments that are later
// consumed by the Python sentiment analyzer.
func Optimize(input Input) Output {
	output := Output{
		Weights:     make([]float64, len(input.Articles)),
		Diagnostics: map[string]float64{},
	}

	now := time.Now().UTC()

	if len(input.Articles) == 0 {
		output.Notes = append(output.Notes, "No articles supplied to optimizer.")
		return output
	}

	stats := map[string]*sourceAggregate{}
	totalAccuracy := 0.0
	totalWeight := 0.0
	accuracySquares := 0.0

	for _, row := range input.History {
		weight := clamp(row.Confidence, 0.05, 1.0)
		if row.Volume > 0 {
			weight += clamp(row.Volume/1e7, 0, 0.35)
		}
		timestamp := parseTime(row.Timestamp)
		if !timestamp.IsZero() {
			ageHours := now.Sub(timestamp).Hours()
			if ageHours < 0 {
				ageHours = 0
			}
			switch {
			case ageHours <= 24:
				weight *= 1.25
			case ageHours <= 168:
				weight *= 1.0
			default:
				weight *= 0.65
			}
		}

		accuracy := row.Sentiment * row.RealizedReturn
		totalAccuracy += accuracy * weight
		totalWeight += weight
		accuracySquares += accuracy * accuracy * weight

		key := normalizeSource(row.Source)
		agg := stats[key]
		if agg == nil {
			agg = &sourceAggregate{}
			stats[key] = agg
		}
		if agg.Original == "" && strings.TrimSpace(row.Source) != "" {
			agg.Original = row.Source
		}
		agg.Accuracy += accuracy * weight
		agg.Weight += weight
		agg.Count++
	}

	notes := []string{}
	if totalWeight > 0 {
		mean := totalAccuracy / totalWeight
		output.BaselineShift = clamp(mean, -0.3, 0.3)
		output.Diagnostics["historical_weight"] = totalWeight
		output.Diagnostics["historical_alignment"] = mean
		variance := 0.0
		if totalWeight > 0 {
			variance = (accuracySquares / totalWeight) - (mean * mean)
			if variance < 0 {
				variance = 0
			}
		}
		output.Diagnostics["historical_variance"] = variance
		switch {
		case variance < 0.01:
			output.ConfidenceAdjustment = 0.08
		case variance < 0.04:
			output.ConfidenceAdjustment = 0.04
		case variance > 0.2:
			output.ConfidenceAdjustment = -0.05
		}
		if output.BaselineShift > 0.05 {
			notes = append(notes, fmt.Sprintf("Sentiment skew trending bullish (+%.2f)", output.BaselineShift))
		} else if output.BaselineShift < -0.05 {
			notes = append(notes, fmt.Sprintf("Sentiment skew trending bearish (%.2f)", output.BaselineShift))
		}
	} else if len(input.History) == 0 {
		notes = append(notes, "No historical sentiment records provided; falling back to recency heuristics.")
	}

	bestSource, bestScore := "", -math.MaxFloat64
	worstSource, worstScore := "", math.MaxFloat64
	for key, agg := range stats {
		score := 0.0
		if agg.Weight > 0 {
			score = agg.Accuracy / agg.Weight
		}
		output.Diagnostics["source:"+key] = score
		if score > bestScore {
			bestSource, bestScore = key, score
		}
		if score < worstScore {
			worstSource, worstScore = key, score
		}
	}

	if bestSource != "" && bestScore > 0 {
		notes = append(notes, fmt.Sprintf("%s historically aligned with price action (+%.2f)", prettifySource(stats[bestSource].Original, bestSource), bestScore))
	}
	if worstSource != "" && worstScore < 0 {
		notes = append(notes, fmt.Sprintf("%s skewed negative historically (%.2f)", prettifySource(stats[worstSource].Original, worstSource), worstScore))
	}

	output.Notes = notes

	for idx, article := range input.Articles {
		baseWeight := article.Weight
		if baseWeight <= 0 {
			baseWeight = 1.0
		}
		sourceFactor := 1.0
		sourceKey := normalizeSource(article.Source)
		if agg, ok := stats[sourceKey]; ok && agg.Weight > 0 {
			score := agg.Accuracy / agg.Weight
			sourceFactor = clamp(1.0+score*0.6, 0.4, 1.6)
		}

		recencyFactor := 1.0
		ts := parseTime(article.PublishedAt)
		if !ts.IsZero() {
			ageHours := now.Sub(ts).Hours()
			if ageHours < 0 {
				ageHours = 0
			}
			switch {
			case ageHours <= 12:
				recencyFactor = 1.18
			case ageHours <= 48:
				recencyFactor = 1.08
			case ageHours >= 120:
				recencyFactor = 0.82
			}
		}

		adjusted := baseWeight * sourceFactor * recencyFactor
		if adjusted < 0.2 {
			adjusted = 0.2
		}
		output.Weights[idx] = adjusted
	}

	return output
}

func clamp(value, minValue, maxValue float64) float64 {
	if value < minValue {
		return minValue
	}
	if value > maxValue {
		return maxValue
	}
	return value
}

func normalizeSource(source string) string {
	trimmed := strings.TrimSpace(strings.ToLower(source))
	if trimmed == "" {
		return "unknown"
	}
	return trimmed
}

func prettifySource(original, fallback string) string {
	candidate := strings.TrimSpace(original)
	if candidate == "" {
		candidate = fallback
	}
	if candidate == "" {
		return "Unknown source"
	}
	parts := strings.FieldsFunc(candidate, func(r rune) bool {
		return r == '_' || r == '-' || r == '.'
	})
	for i, part := range parts {
		part = strings.ToLower(part)
		if len(part) == 0 {
			continue
		}
		parts[i] = strings.ToUpper(part[:1]) + part[1:]
	}
	return strings.Join(parts, " ")
}

func parseTime(value string) time.Time {
	trimmed := strings.TrimSpace(value)
	if trimmed == "" {
		return time.Time{}
	}
	// Try RFC3339 / ISO8601 first.
	if ts, err := time.Parse(time.RFC3339, trimmed); err == nil {
		return ts.UTC()
	}
	layouts := []string{
		"2006-01-02 15:04:05",
		"2006-01-02",
	}
	for _, layout := range layouts {
		if ts, err := time.Parse(layout, trimmed); err == nil {
			return ts.UTC()
		}
	}
	if numeric, err := strconv.ParseFloat(trimmed, 64); err == nil {
		if numeric > 1e12 {
			numeric = numeric / 1000
		}
		if numeric > 0 {
			return time.Unix(int64(numeric), 0).UTC()
		}
	}
	return time.Time{}
}
