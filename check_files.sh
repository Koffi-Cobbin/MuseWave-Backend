#!/bin/bash

echo "======================================"
echo "Django Music Backend - File Checker"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Not in django-music-backend directory!"
    echo "Please run: cd django-music-backend"
    exit 1
fi

echo "✅ In correct directory"
echo ""

# Count files
echo "📊 File Statistics:"
echo "-------------------"

py_files=$(find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" | wc -l)
md_files=$(find . -name "*.md" | wc -l)
total_files=$(find . -type f -not -path "./.venv/*" -not -path "./venv/*" -not -path "./.git/*" | wc -l)

echo "Python files: $py_files"
echo "Markdown docs: $md_files"
echo "Total files: $total_files"
echo ""

# Check key files
echo "🔍 Checking Key Files:"
echo "---------------------"

files=(
    "manage.py"
    "requirements.txt"
    "config/settings.py"
    "musewave/models.py"
    "musewave/views.py"
    "musewave/serializers.py"
    "musewave/urls.py"
    "musewave/admin.py"
    "README.md"
)

all_present=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        size=$(wc -c < "$file")
        printf "✅ %-30s (%s bytes)\n" "$file" "$size"
    else
        printf "❌ %-30s (MISSING!)\n" "$file"
        all_present=false
    fi
done

echo ""

if [ "$all_present" = true ]; then
    echo "✅ All key files present!"
    echo ""
    echo "🎉 Ready to start! Run:"
    echo "   ./quickstart.sh"
    echo ""
else
    echo "❌ Some files are missing!"
    echo "Please re-download the django-music-backend folder."
fi

echo "======================================"
