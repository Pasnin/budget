import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title='Budget Analyzer',
    page_icon='💰',
    layout='wide'
)

# Global Constants
DEFAULT_CURRENCY = 'NOK'
INCOME_CATEGORIES = ['Salary', 'Side Income', 'Investments', 'Other Income']
EXPENSE_CATEGORIES = {
    'Housing': ['Rent/Mortgage', 'Utilities', 'Internet', 'Maintenance'],
    'Transportation': ['Public Transport', 'Car Expenses', 'Fuel', 'Car Insurance', 'Car Maintenance'],
    'Food': ['Groceries', 'Eating Out', 'Food Delivery'],
    'Entertainment': ['Streaming Services', 'Movies/Events', 'Hobbies'],
    'Health': ['Insurance', 'Medication', 'Gym/Fitness'],
    'Personal': ['Clothing', 'Haircuts', 'Personal Care'],
    'Education': ['Courses', 'Books', 'School Fees'],
    'Savings': ['Emergency Fund', 'Investment Savings', 'Retirement'],
    'Debt': ['Student Loans', 'Credit Card', 'Other Loans'],
    'Other': ['Gifts', 'Charity', 'Miscellaneous']
}

# Default values in NOK for common expenses in Norway
DEFAULT_VALUES = {
    'Salary': 45000,
    'Side Income': 0,
    'Investments': 0,
    'Other Income': 0,
    'Rent/Mortgage': 12000,
    'Utilities': 1200,
    'Internet': 550,
    'Maintenance': 500,
    'Public Transport': 800,
    'Car Expenses': 0,
    'Fuel': 0,
    'Car Insurance': 0,
    'Car Maintenance': 0,
    'Groceries': 4000,
    'Eating Out': 1500,
    'Food Delivery': 800,
    'Streaming Services': 400,
    'Movies/Events': 600,
    'Hobbies': 800,
    'Insurance': 400,
    'Medication': 200,
    'Gym/Fitness': 500,
    'Clothing': 1000,
    'Haircuts': 400,
    'Personal Care': 500,
    'Courses': 0,
    'Books': 300,
    'School Fees': 0,
    'Emergency Fund': 2000,
    'Investment Savings': 1500,
    'Retirement': 1000,
    'Student Loans': 0,
    'Credit Card': 0,
    'Other Loans': 0,
    'Gifts': 500,
    'Charity': 300,
    'Miscellaneous': 1000
}

# Functions for data handling
def load_budget_data():
    """Load budget data from file or return default data."""
    if os.path.exists('budget_data.json'):
        with open('budget_data.json', 'r') as f:
            return json.load(f)
    
    # Return default data structure
    budget_data = {
        'income': {category: DEFAULT_VALUES.get(category, 0) for category in INCOME_CATEGORIES},
        'expenses': {}
    }
    
    for category, subcategories in EXPENSE_CATEGORIES.items():
        budget_data['expenses'][category] = {
            subcategory: DEFAULT_VALUES.get(subcategory, 0) for subcategory in subcategories
        }
    
    return budget_data

def save_budget_data(data):
    """Save budget data to file."""
    with open('budget_data.json', 'w') as f:
        json.dump(data, f, indent=4)

def get_total_income(income_data):
    """Calculate total income."""
    return sum(income_data.values())

def get_total_expenses(expenses_data):
    """Calculate total expenses from all categories."""
    total = 0
    for category, subcategories in expenses_data.items():
        total += sum(subcategories.values())
    return total

def get_savings(income, expenses):
    """Calculate savings amount."""
    return income - expenses

def get_expense_breakdown(expenses_data):
    """Transform expenses data for visualization."""
    data = []
    for category, subcategories in expenses_data.items():
        category_total = sum(subcategories.values())
        data.append({
            'Category': category,
            'Amount': category_total
        })
        for subcategory, amount in subcategories.items():
            if amount > 0:  # Only include subcategories with expenses
                data.append({
                    'Category': f"{category} - {subcategory}",
                    'Amount': amount,
                    'Parent': category
                })
    
    return pl.DataFrame(data)

# Main application
def main():
    st.title('💰 Budget Analyzer')
    
    # Load budget data
    budget_data = load_budget_data()
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(['📊 Dashboard', '📝 Edit Budget', '💾 Save/Load'])
    
    # Dashboard Tab
    with tab1:
        st.header('Budget Dashboard')
        
        # Calculate key metrics
        total_income = get_total_income(budget_data['income'])
        total_expenses = get_total_expenses(budget_data['expenses'])
        savings = get_savings(total_income, total_expenses)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="Total Income", value=f"{total_income:,.0f} {DEFAULT_CURRENCY}")
        col2.metric(label="Total Expenses", value=f"{total_expenses:,.0f} {DEFAULT_CURRENCY}")
        col3.metric(label="Savings", value=f"{savings:,.0f} {DEFAULT_CURRENCY}")
        col4.metric(label="Savings Rate", value=f"{(savings/total_income*100 if total_income > 0 else 0):.1f}%")
        
        st.subheader('Income vs. Expenses')
        summary_data = pl.DataFrame({
            'Category': ['Income', 'Expenses', 'Savings'],
            'Amount': [total_income, total_expenses, savings]
        })
        
        fig = px.bar(summary_data.to_pandas(), x='Category', y='Amount', color='Category',
                    color_discrete_map={'Income': 'green', 'Expenses': 'red', 'Savings': 'blue'},
                    title='Income vs. Expenses')
        fig.update_layout(yaxis_title=f'Amount ({DEFAULT_CURRENCY})')
        st.plotly_chart(fig, use_container_width=True)
        
        # Expense breakdown
        st.subheader('Expense Breakdown')
        if total_expenses > 0:
            expense_df = get_expense_breakdown(budget_data['expenses'])
            main_categories = expense_df.filter(~pl.col('Category').str.contains(' - ')).sort('Amount', descending=True)
            
            fig1 = px.pie(main_categories.to_pandas(), values='Amount', names='Category', 
                        title='Expense Distribution by Category')
            st.plotly_chart(fig1, use_container_width=True)
            
            # Top expenses
            st.subheader('Top 10 Expenses')
            top_expenses = expense_df.filter(pl.col('Category').str.contains(' - ')).sort('Amount', descending=True).head(10)
            fig2 = px.bar(top_expenses.to_pandas(), x='Amount', y='Category', orientation='h',
                        title='Top 10 Individual Expenses')
            fig2.update_layout(xaxis_title=f'Amount ({DEFAULT_CURRENCY})', yaxis_title='')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info('No expense data to display. Please add expenses in the Edit Budget tab.')
    
    # Edit Budget Tab
    with tab2:
        st.header('Edit Your Budget')
        
        # Income Section
        st.subheader('Income')
        income_cols = st.columns(len(INCOME_CATEGORIES))
        
        for i, category in enumerate(INCOME_CATEGORIES):
            with income_cols[i]:
                budget_data['income'][category] = st.number_input(
                    f"{category} ({DEFAULT_CURRENCY})",
                    min_value=0,
                    value=budget_data['income'][category],
                    step=100
                )
        
        # Expenses Section
        st.subheader('Expenses')
        
        for category, subcategories in EXPENSE_CATEGORIES.items():
            with st.expander(f"{category}"):
                subcategory_cols = st.columns(2)  # Two columns for subcategories
                
                for i, subcategory in enumerate(subcategories):
                    with subcategory_cols[i % 2]:
                        budget_data['expenses'][category][subcategory] = st.number_input(
                            f"{subcategory} ({DEFAULT_CURRENCY})",
                            min_value=0,
                            value=budget_data['expenses'][category][subcategory],
                            step=100
                        )
        
        # Save changes
        if st.button('Update Budget'):
            save_budget_data(budget_data)
            st.success('Budget updated successfully!')
    
    # Save/Load Tab
    with tab3:
        st.header('Save or Load Budget Data')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader('Save Current Budget')
            save_name = st.text_input('Budget Name', f'Budget_{datetime.now().strftime("%Y%m%d")}')
            
            if st.button('Save Budget'):
                file_path = f"{save_name}.json"
                with open(file_path, 'w') as f:
                    json.dump(budget_data, f, indent=4)
                st.success(f'Budget saved as {file_path}!')
        
        with col2:
            st.subheader('Load Saved Budget')
            saved_files = [f for f in os.listdir('.') if f.endswith('.json')]
            
            if saved_files:
                selected_file = st.selectbox('Select a saved budget', saved_files)
                
                if st.button('Load Selected Budget'):
                    try:
                        with open(selected_file, 'r') as f:
                            loaded_data = json.load(f)
                        save_budget_data(loaded_data)
                        st.success(f'Budget loaded from {selected_file}!')
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f'Error loading budget: {e}')
            else:
                st.info('No saved budgets found.')
        
        st.subheader('Reset to Default')
        if st.button('Reset to Default Values'):
            if os.path.exists('budget_data.json'):
                os.remove('budget_data.json')
            st.success('Budget reset to default values!')
            st.experimental_rerun()

if __name__ == '__main__':
    main() 