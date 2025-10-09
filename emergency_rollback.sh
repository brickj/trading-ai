#!/bin/bash
# Emergency rollback script for navbar changes
# This script restores the current working version

echo "🚨 EMERGENCY ROLLBACK - RESTORING PREVIOUS WORKING VERSION"
echo "========================================================="

# Restore navbar template
if [ -f "src/web/templates/navbar.html.current_backup" ]; then
    cp src/web/templates/navbar.html.current_backup src/web/templates/navbar.html
    echo "✅ Restored navbar.html from current backup"
else
    echo "❌ navbar.html.current_backup not found"
fi

# Restore styles.css
if [ -f "src/web/static/css/styles.css.current_backup" ]; then
    cp src/web/static/css/styles.css.current_backup src/web/static/css/styles.css
    echo "✅ Restored styles.css from current backup"
else
    echo "❌ styles.css.current_backup not found"
fi

echo ""
echo "🔄 ROLLBACK COMPLETE!"
echo "====================="
echo "The navbar has been restored to the previous working version."
echo "Please refresh your browser to see the changes."
