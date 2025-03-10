# Budget Analyzer

A Streamlit web application for managing and analyzing personal budgets in Norwegian Crowns (NOK). The application supports multiple users, with each user having their own budget data.

## Features

- **Multi-User Support**: Each user has their own budget data and presets
- **User Authentication**: Simple username/password login system
- **Dashboard**: Visualize your income, expenses, and savings
- **Multiple Expense Categories**: Track spending across various categories
- **Customizable**: Edit default values to match your personal financial situation
- **Presets**: Save different budget configurations as presets and load them when needed
- **Data Persistence**: Budget data is automatically saved between sessions

## Default Data

The application comes with predefined default values for common income and expense categories in Norway (in NOK). These values serve as reasonable starting points but should be adjusted to match your personal financial situation.

## Installation

1. Clone the repository:
```
git clone https://github.com/Pasnin/budget.git
cd budget
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Run the Streamlit app:
```
streamlit run app.py
```

## Usage

### User Authentication

1. Create a new account by entering a username and password, then clicking "Create New Account"
2. Login to an existing account by entering your username and password, then clicking "Login"

### Main Features

The application consists of three main tabs:

1. **Dashboard**: View visualizations of your budget including income vs. expenses, expense breakdown by category, and your top expenses.

2. **Edit Budget**: Update your income and expense values. Changes are saved when you click the "Update Budget" button.

3. **Save/Load**: Save your current budget configuration as a preset with a custom name or load a previously saved preset. You can also reset to default values.

## Requirements

- Python 3.7+
- Streamlit
- Polars
- Plotly

## License

MIT

## Author

Pasnin 