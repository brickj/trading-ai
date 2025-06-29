#!/usr/bin/env python3

def fix_indentation():
    file_path = 'src/web/app.py'
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Fix the indentation issue around line 1960-1970
    for i in range(len(lines)):
        if "else:" in lines[i] and "sentiment_result = sentiment_analyzer.analyze_news_sentiment" in lines[i+1]:
            # This is the problematic area
            lines[i] = "            else:\n"
            break
    
    with open(file_path, 'w') as file:
        file.writelines(lines)
    
    print("Indentation fixed in", file_path)

if __name__ == "__main__":
    fix_indentation()
