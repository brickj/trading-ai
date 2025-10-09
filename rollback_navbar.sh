#!/bin/bash
# Rollback script for navbar changes
# This script restores the original navbar CSS

echo "🔄 ROLLING BACK NAVBAR CHANGES"
echo "==============================="

# Check if backup exists
if [ -f "src/web/static/css/styles.css.backup" ]; then
    echo "✅ Found backup file: styles.css.backup"
    
    # Restore the backup
    cp src/web/static/css/styles.css.backup src/web/static/css/styles.css
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully restored original navbar CSS"
        echo "✅ Navbar is back to single-row layout"
        echo ""
        echo "🔄 Please refresh your browser to see the changes"
    else
        echo "❌ Failed to restore backup"
        exit 1
    fi
else
    echo "❌ Backup file not found: styles.css.backup"
    echo "❌ Cannot rollback changes"
    exit 1
fi

echo ""
echo "🎉 ROLLBACK COMPLETE!"
echo "====================="
echo "The navbar has been restored to its original single-row layout."
echo ""
echo "📝 What was reverted:"
echo "   - Removed section header line breaks"
echo "   - Removed order properties"
echo "   - Restored original flex-wrap behavior"
