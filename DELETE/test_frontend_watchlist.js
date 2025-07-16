// Test script to check watchlist API response
async function testWatchlistAPI() {
    console.log('Testing watchlist API...');
    
    try {
        const response = await fetch('/api/watchlist_opportunities');
        const data = await response.json();
        
        console.log('Raw API response:', data);
        console.log('Data structure:', {
            hasData: !!data.data,
            dataKeys: data.data ? Object.keys(data.data) : [],
            opportunities: data.data?.opportunities || [],
            opportunitiesLength: data.data?.opportunities?.length || 0,
            count: data.data?.count || 0,
            cached: data.data?.cached || false
        });
        
        // Test the filtering logic
        const responseData = data.data || data;
        const opportunities = responseData.opportunities || [];
        
        console.log('Extracted opportunities:', opportunities);
        console.log('Opportunities length:', opportunities.length);
        
        if (opportunities.length > 0) {
            const opp = opportunities[0];
            console.log('First opportunity:', opp);
            
            // Test filtering conditions
            const hasPrice = opp.price_data?.current_price > 0;
            const hasSentiment = opp.sentiment_data?.confidence > 0;
            const hasSignal = opp.signal_data?.action && opp.signal_data.action !== 'HOLD';
            const hasNews = opp.news_count > 0;
            
            console.log('Filtering conditions:', {
                hasPrice,
                hasSentiment,
                hasSignal,
                hasNews,
                isMeaningful: hasPrice || hasSentiment || hasSignal || hasNews,
                priceValue: opp.price_data?.current_price,
                sentimentConfidence: opp.sentiment_data?.confidence,
                signalAction: opp.signal_data?.action,
                newsCount: opp.news_count
            });
        }
        
    } catch (error) {
        console.error('Error testing API:', error);
    }
}

// Run the test
testWatchlistAPI(); 