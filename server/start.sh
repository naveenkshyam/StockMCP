#!/bin/bash
# Quick Start Script for Stock Analysis System

echo "========================================================================"
echo "STOCK ANALYSIS SYSTEM - QUICK START"
echo "========================================================================"
echo ""
echo "This system provides:"
echo "  ✓ Real-time stock analysis with buy/sell recommendations"
echo "  ✓ News sentiment integration for better predictions"
echo "  ✓ Top recommendations with 50-point scoring system"
echo "  ✓ 3-month historical performance tracking"
echo "  ✓ Email notifications and automated reports"
echo "  ✓ Configurable stock lists and settings"
echo ""
echo "========================================================================"
echo ""

# Check if in correct directory
if [ ! -f "run.py" ]; then
    echo "❌ Error: Please run this from the server directory"
    echo "   cd /home/nshyam/lambda-examples/ML_Python_examples/StockMCP/server"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Please set up the environment first"
    exit 1
fi

echo "Choose how to start:"
echo ""
echo "1. Interactive Menu (Recommended for beginners)"
echo "   • User-friendly interface"
echo "   • Guided through all options"
echo ""
echo "2. Command Line Interface (For quick tasks)"
echo "   • Direct access to features"
echo "   • Scriptable and automatable"
echo ""
echo "3. Run Tests (Verify everything works)"
echo "   • Quick smoke test"
echo "   • Or full test suite"
echo ""
echo "4. View Documentation"
echo ""
echo "5. Exit"
echo ""

read -p "Select option (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Starting interactive menu..."
        echo ""
        source .venv/bin/activate
        python run.py
        ;;
    2)
        echo ""
        echo "Command Line Interface - Examples:"
        echo ""
        echo "# Analyze stocks from config list"
        echo "python feature_manager.py analyze --list penny --top 10"
        echo ""
        echo "# Historical analysis"
        echo "python feature_manager.py historical --min-performance 10"
        echo ""
        echo "# Send email report"
        echo "python feature_manager.py email --list default"
        echo ""
        echo "For full help:"
        source .venv/bin/activate
        python feature_manager.py --help
        ;;
    3)
        echo ""
        echo "Choose test type:"
        echo "1. Quick smoke test (fast)"
        echo "2. Full test suite (comprehensive)"
        echo ""
        read -p "Select (1-2): " test_choice
        
        source .venv/bin/activate
        if [ "$test_choice" = "1" ]; then
            python test_all_features.py --quick
        else
            python test_all_features.py
        fi
        ;;
    4)
        echo ""
        echo "Documentation files:"
        echo "  • README.md - Quick start and usage guide"
        echo "  • FINAL_STRUCTURE.md - System structure overview"
        echo "  • config.yaml - Configuration file"
        echo ""
        read -p "Open README.md? (y/n): " open_readme
        if [ "$open_readme" = "y" ]; then
            ${EDITOR:-nano} README.md
        fi
        ;;
    5)
        echo ""
        echo "Goodbye!"
        echo ""
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid option. Please run again and select 1-5."
        exit 1
        ;;
esac
