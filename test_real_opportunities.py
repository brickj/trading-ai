import pytest
from playwright.sync_api import Page, expect
import time

# Define the base URL for the application
BASE_URL = "http://localhost:5001"

def test_real_opportunities_page(page: Page):
    """
    Test the real opportunities page without any mock data.
    This will show us what's actually being displayed.
    This version takes multiple screenshots and thoroughly checks data population.
    """
    
    # Track all network requests
    api_calls = []
    page.on("request", lambda request: api_calls.append({
        "url": request.url,
        "method": request.method
    }))
    
    # Track all network responses
    api_responses = []
    page.on("response", lambda response: api_responses.append({
        "url": response.url,
        "status": response.status,
        "headers": dict(response.headers)
    }))
    
    # Capture all console messages
    console_messages = []
    page.on("console", lambda msg: console_messages.append({
        "type": msg.type,
        "text": msg.text
    }))
    
    # Navigate to the opportunities page
    page.goto(f"{BASE_URL}/opportunities")
    
    # Take screenshot of initial page load
    page.screenshot(path="test_step1_initial_page.png")
    print("📸 Screenshot taken: test_step1_initial_page.png")
    
    # Wait for the page to load
    page.wait_for_load_state("networkidle")
    
    # Click the "All" button to trigger data loading
    page.locator("#allBtn").click()
    
    # Wait for the second API call to complete (the "all" opportunities call)
    with page.expect_response("**/api/all_opportunities"):
        pass
    
    # Wait a bit more for the frontend to process the response
    page.wait_for_timeout(3000)
    
    # Take screenshot after data loading
    page.screenshot(path="test_step2_after_data_load.png")
    print("📸 Screenshot taken: test_step2_after_data_load.png")
    
    # Print all API calls made
    print("\n=== API CALLS MADE ===")
    for call in api_calls:
        if "api" in call["url"]:
            print(f"API Call: {call['method']} {call['url']}")
    
    # Print all API responses
    print("\n=== API RESPONSES ===")
    for response in api_responses:
        if "api" in response["url"]:
            print(f"API Response: {response['status']} {response['url']}")
            try:
                response_text = response.text()
                print(f"Response body: {response_text[:500]}...")
            except:
                print("Could not read response body")
    
    # Print all console messages
    print("\n=== BROWSER CONSOLE MESSAGES ===")
    for msg in console_messages:
        if msg["type"] in ["log", "error", "warn"]:
            print(f"[{msg['type'].upper()}] {msg['text']}")
    
    # Check what's actually in the container
    container = page.locator("#opportunitiesContainer")
    container_html = container.inner_html()
    print(f"\nContainer HTML: {container_html}")
    
    # Wait for the debug panel to show the last API request and response
    try:
        debug_request = page.wait_for_selector('#debugApiRequest', timeout=10000)
        debug_response = page.wait_for_selector('#debugApiResponse', timeout=10000)
        request_text = page.locator('#debugApiRequest').inner_text()
        response_text = page.locator('#debugApiResponse').inner_text()
        print(f"Debug Panel - Last API Request: {request_text}")
        print(f"Debug Panel - Last API Response: {response_text[:200]}...")
        assert request_text and request_text != '(none)', "Debug panel did not capture the last API request URL!"
        assert response_text and response_text.strip() != '', "Debug panel did not capture the last API response!"
    except Exception as e:
        print(f"❌ Debug panel not found or not populated: {e}")
        print(f"Page content:\n{page.content()[:1000]}...")
        page.screenshot(path="test_failed_debug_panel.png")
        print("📸 Screenshot taken: test_failed_debug_panel.png")
        assert False, f"Debug panel not found or not populated: {e}"

    # Check for empty state message first
    empty_state = page.locator("h5:has-text('No trading opportunities found')")
    empty_state_count = empty_state.count()
    print(f"Empty state message count: {empty_state_count}")

    # Count opportunity cards
    opportunity_cards = page.locator(".opportunity-card")
    card_count = opportunity_cards.count()
    print(f"Number of opportunity cards found: {card_count}")

    # Fail if empty state is present or no cards are found
    if empty_state_count > 0 or card_count == 0:
        print("❌ UI is empty: either empty state is present or no cards found!")
        container_html = page.locator("#opportunitiesContainer").inner_html()
        print(f"Container HTML: {container_html}")
        page.screenshot(path="test_failed_empty_state.png")
        print("📸 Screenshot taken: test_failed_empty_state.png")
        assert False, "UI is empty: no opportunity cards are displayed!"
    
    # Track what we found for detailed reporting
    found_symbols = []
    found_actions = []
    found_types = []
    data_validation_results = []
    
    # For each card, check all required fields and verify specific data
    for i in range(card_count):
        card = opportunity_cards.nth(i)
        print(f"\n--- Checking Card {i+1} ---")
        
        # Take screenshot of individual card
        card.screenshot(path=f"test_card_{i+1}_detail.png")
        print(f"📸 Screenshot taken: test_card_{i+1}_detail.png")
        
        # Get symbol
        symbol_element = card.locator(".card-header strong").first
        symbol = symbol_element.inner_text()
        found_symbols.append(symbol)
        print(f"Symbol: {symbol}")
        expect(symbol_element).to_be_visible()
        assert symbol, f"Symbol is empty in card {i+1}"
        
        # Check type badge (Stock or Crypto)
        type_badges = card.locator(".badge")
        stock_badges = card.locator(".badge:has-text('Stock')")
        crypto_badges = card.locator(".badge:has-text('Crypto')")
        
        if stock_badges.count() > 0:
            found_types.append("Stock")
            print("Type: Stock")
        elif crypto_badges.count() > 0:
            found_types.append("Crypto")
            print("Type: Crypto")
        else:
            print("❌ No type badge found!")
            data_validation_results.append(f"Card {i+1}: Missing type badge")
            assert False, f"No type badge found in card {i+1}"
        
        # Check trigger badge (News-Driven or Watchlist)
        news_driven_badges = card.locator(".badge:has-text('News-Driven')")
        watchlist_badges = card.locator(".badge:has-text('Watchlist')")
        
        if news_driven_badges.count() > 0:
            print("Trigger: News-Driven")
        elif watchlist_badges.count() > 0:
            print("Trigger: Watchlist")
        else:
            print("❌ No trigger badge found!")
            data_validation_results.append(f"Card {i+1}: Missing trigger badge")
            assert False, f"No trigger badge found in card {i+1}"
        
        # Check action badge (CALL, PUT, HOLD, SELL)
        call_badges = card.locator(".badge:has-text('CALL')")
        put_badges = card.locator(".badge:has-text('PUT')")
        hold_badges = card.locator(".badge:has-text('HOLD')")
        sell_badges = card.locator(".badge:has-text('SELL')")
        
        if call_badges.count() > 0:
            found_actions.append("CALL")
            print("Action: CALL")
        elif put_badges.count() > 0:
            found_actions.append("PUT")
            print("Action: PUT")
        elif hold_badges.count() > 0:
            found_actions.append("HOLD")
            print("Action: HOLD")
        elif sell_badges.count() > 0:
            found_actions.append("SELL")
            print("Action: SELL")
        else:
            print("❌ No action badge found!")
            data_validation_results.append(f"Card {i+1}: Missing action badge")
            assert False, f"No action badge found in card {i+1}"
        
        # Check price information - VERIFY ACTUAL DATA
        current_price_element = card.locator(".col-md-3:nth-child(1) p:has-text('Current:')")
        current_price_text = current_price_element.inner_text()
        print(f"Current Price: {current_price_text}")
        
        if "N/A" in current_price_text or "$0" in current_price_text or not "$" in current_price_text:
            print("❌ Current price is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid current price - {current_price_text}")
            assert False, f"Current price should contain valid $ amount, got: {current_price_text}"
        
        strike_price_element = card.locator(".col-md-3:nth-child(1) p:has-text('Strike:')")
        strike_price_text = strike_price_element.inner_text()
        print(f"Strike Price: {strike_price_text}")
        
        if "N/A" in strike_price_text or "$0" in strike_price_text or not "$" in strike_price_text:
            print("❌ Strike price is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid strike price - {strike_price_text}")
            assert False, f"Strike price should contain valid $ amount, got: {strike_price_text}"
        
        option_price_element = card.locator(".col-md-3:nth-child(1) p:has-text('Option Price:')")
        option_price_text = option_price_element.inner_text()
        print(f"Option Price: {option_price_text}")
        
        if "N/A" in option_price_text or "$0" in option_price_text or not "$" in option_price_text:
            print("❌ Option price is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid option price - {option_price_text}")
            assert False, f"Option price should contain valid $ amount, got: {option_price_text}"
        
        # Check sentiment information - VERIFY ACTUAL DATA
        sentiment_score_element = card.locator(".col-md-3:nth-child(2) p:has-text('Score:')")
        sentiment_score_text = sentiment_score_element.inner_text()
        print(f"Sentiment Score: {sentiment_score_text}")
        
        if "N/A" in sentiment_score_text or "0.000" in sentiment_score_text:
            print("❌ Sentiment score is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid sentiment score - {sentiment_score_text}")
            assert False, f"Sentiment score should be meaningful, got: {sentiment_score_text}"
        
        confidence_element = card.locator(".col-md-3:nth-child(2) p:has-text('Confidence:')")
        confidence_text = confidence_element.inner_text()
        print(f"Confidence: {confidence_text}")
        
        if "N/A" in confidence_text or confidence_text == "Confidence: 0%":
            print("❌ Confidence is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid confidence - {confidence_text}")
            assert False, f"Confidence should be meaningful, got: {confidence_text}"
        
        news_count_element = card.locator(".col-md-3:nth-child(2) p:has-text('News Count:')")
        news_count_text = news_count_element.inner_text()
        print(f"News Count: {news_count_text}")
        
        if "N/A" in news_count_text or news_count_text == "News Count: 0":
            print("❌ News count is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid news count - {news_count_text}")
            assert False, f"News count should be meaningful, got: {news_count_text}"
        
        # Check trade details - VERIFY ACTUAL DATA
        position_size_element = card.locator(".col-md-3:nth-child(3) p:has-text('Position Size:')")
        position_size_text = position_size_element.inner_text()
        print(f"Position Size: {position_size_text}")
        
        if "N/A" in position_size_text or "0" in position_size_text:
            print("❌ Position size is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid position size - {position_size_text}")
            assert False, f"Position size should be meaningful, got: {position_size_text}"
        
        total_cost_element = card.locator(".col-md-3:nth-child(3) p:has-text('Total Cost:')")
        total_cost_text = total_cost_element.inner_text()
        print(f"Total Cost: {total_cost_text}")
        
        if "N/A" in total_cost_text or "$0" in total_cost_text or not "$" in total_cost_text:
            print("❌ Total cost is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid total cost - {total_cost_text}")
            assert False, f"Total cost should contain valid $ amount, got: {total_cost_text}"
        
        signal_strength_element = card.locator(".col-md-3:nth-child(3) p:has-text('Signal Strength:')")
        signal_strength_text = signal_strength_element.inner_text()
        print(f"Signal Strength: {signal_strength_text}")
        
        if "N/A" in signal_strength_text or "0.000" in signal_strength_text:
            print("❌ Signal strength is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid signal strength - {signal_strength_text}")
            assert False, f"Signal strength should be meaningful, got: {signal_strength_text}"
        
        # Check reasoning - VERIFY ACTUAL DATA
        reasoning_element = card.locator(".col-md-3:nth-child(4) p.small")
        reasoning_text = reasoning_element.inner_text()
        print(f"Reasoning: {reasoning_text[:100]}...")
        
        if "No reasoning provided" in reasoning_text or len(reasoning_text.strip()) < 10:
            print("❌ Reasoning is invalid!")
            data_validation_results.append(f"Card {i+1}: Invalid reasoning - too short or empty")
            assert False, f"Reasoning should be meaningful, got: {reasoning_text[:50]}"
        
        # Check for execute button
        execute_button = card.locator("button:has-text('Execute')")
        if execute_button.count() == 0:
            print("❌ Execute button missing!")
            data_validation_results.append(f"Card {i+1}: Missing execute button")
            assert False, f"Execute button should be present in card {i+1}"
        else:
            expect(execute_button).to_be_visible()
            print("Execute button: Present")
    
    # Summary of what we found
    print(f"\n=== SUMMARY ===")
    print(f"Total cards found: {card_count}")
    print(f"Symbols found: {found_symbols}")
    print(f"Types found: {found_types}")
    print(f"Actions found: {found_actions}")
    
    # Verify we have meaningful data
    assert len(set(found_symbols)) >= 1, f"Should have at least 1 symbol, got: {found_symbols}"
    assert len(set(found_types)) >= 1, f"Should have at least 1 type, got: {found_types}"
    assert len(set(found_actions)) >= 1, f"Should have at least 1 action, got: {found_actions}"
    
    # Log what we found for debugging
    print(f"\n=== TEST RESULTS ===")
    print(f"✅ Found {len(set(found_symbols))} unique symbols: {found_symbols}")
    print(f"✅ Found {len(set(found_types))} types: {found_types}")
    print(f"✅ Found {len(set(found_actions))} actions: {found_actions}")
    print(f"✅ Total opportunities displayed: {card_count}")
    
    if data_validation_results:
        print(f"❌ Data validation issues found: {data_validation_results}")
        assert False, f"Data validation failed: {data_validation_results}"
    
    # Take final success screenshot
    page.screenshot(path="test_success_fully_populated.png")
    print("📸 Screenshot taken: test_success_fully_populated.png")
    
    print("\n✅ Test completed successfully! Page is fully populated with real data!")
    print("📸 Check screenshots for visual proof:")
    print("   - test_step1_initial_page.png")
    print("   - test_step2_after_data_load.png")
    print("   - test_card_1_detail.png")
    print("   - test_success_fully_populated.png") 