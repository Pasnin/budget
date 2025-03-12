import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import hashlib
from datetime import datetime
import io

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

# Make sure the data directory exists
if not os.path.exists('user_data'):
    os.makedirs('user_data')

# User authentication and session management
def get_user_id():
    """Get or create a user ID for the session"""
    if 'user_id' not in st.session_state:
        # User login section
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
            st.session_state.username = ''
            
        if not st.session_state.logged_in:
            st.sidebar.title('User Login')
            username = st.sidebar.text_input('Username')
            password = st.sidebar.text_input('Password', type='password')
            
            if st.sidebar.button('Login'):
                if username and password:  # Simple validation
                    # Create a hash of the username for the user ID
                    user_id = hashlib.md5(username.encode()).hexdigest()
                    st.session_state.user_id = user_id
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.sidebar.success(f'Welcome, {username}!')
                    st.rerun()
                else:
                    st.sidebar.error('Please enter a username and password')
            
            # Option to create a new account
            if st.sidebar.button('Create New Account'):
                if username and password:
                    user_id = hashlib.md5(username.encode()).hexdigest()
                    st.session_state.user_id = user_id
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.sidebar.success(f'Account created! Welcome, {username}!')
                    # Create default budget for new user
                    default_budget = get_default_budget()
                    save_budget_data(default_budget, user_id)
                    st.rerun()
                else:
                    st.sidebar.error('Please enter a username and password')
            
            # Hide the main content until logged in
            st.stop()
    
    return st.session_state.user_id

# Functions for data handling
def get_default_budget():
    """Return default budget data structure."""
    budget_data = {
        'income': {category: DEFAULT_VALUES.get(category, 0) for category in INCOME_CATEGORIES},
        'expenses': {}
    }
    
    for category, subcategories in EXPENSE_CATEGORIES.items():
        budget_data['expenses'][category] = {
            subcategory: DEFAULT_VALUES.get(subcategory, 0) for subcategory in subcategories
        }
    
    return budget_data

def get_user_file_path(user_id):
    """Get the file path for a user's budget data."""
    return os.path.join('user_data', f'{user_id}.json')

def load_budget_data(user_id=None):
    """Load budget data from file or return default data."""
    if user_id is None:
        user_id = get_user_id()
        
    file_path = get_user_file_path(user_id)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    
    # Return default data structure if no file exists
    return get_default_budget()

def save_budget_data(data, user_id=None):
    """Save budget data to file."""
    if user_id is None:
        user_id = get_user_id()
        
    file_path = get_user_file_path(user_id)
    
    with open(file_path, 'w') as f:
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

def generate_savings_suggestions(budget_data):
    """Generate personalized savings suggestions based on budget data."""
    income_data = budget_data['income']
    expenses_data = budget_data['expenses']
    
    total_income = get_total_income(income_data)
    total_expenses = get_total_expenses(expenses_data)
    current_savings = get_savings(total_income, total_expenses)
    savings_rate = (current_savings / total_income * 100) if total_income > 0 else 0
    
    # Get expense breakdown
    expense_df = get_expense_breakdown(expenses_data)
    main_categories = expense_df.filter(~pl.col('Category').str.contains(' - ')).sort('Amount', descending=True)
    subcategories = expense_df.filter(pl.col('Category').str.contains(' - ')).sort('Amount', descending=True)
    
    suggestions = []
    
    # Suggestion 1: Overall savings rate recommendation
    if savings_rate < 20:
        suggestions.append({
            'title': 'Increase Your Savings Rate',
            'description': f'Your current savings rate is {savings_rate:.1f}%. Financial experts recommend saving at least 20% of your income. Consider ways to increase your income or reduce expenses.',
            'potential_savings': total_income * 0.2 - current_savings if current_savings < total_income * 0.2 else 0
        })
    
    # Suggestion 2: Housing cost recommendation
    housing_expenses = expenses_data.get('Housing', {})
    housing_total = sum(housing_expenses.values())
    housing_pct = (housing_total / total_income * 100) if total_income > 0 else 0
    
    if housing_pct > 30:
        suggestions.append({
            'title': 'Reduce Housing Costs',
            'description': f'Your housing costs are {housing_pct:.1f}% of your income. The recommended maximum is 30%. Consider ways to reduce housing expenses.',
            'potential_savings': housing_total - (total_income * 0.3) if housing_total > total_income * 0.3 else 0
        })
    
    # Suggestion 3: Food expenses
    food_expenses = expenses_data.get('Food', {})
    eating_out = food_expenses.get('Eating Out', 0) + food_expenses.get('Food Delivery', 0)
    groceries = food_expenses.get('Groceries', 0)
    
    if eating_out > groceries * 0.5 and eating_out > 0:
        suggestions.append({
            'title': 'Reduce Dining Out Expenses',
            'description': f'You\'re spending {(eating_out / (eating_out + groceries) * 100):.1f}% of your food budget on dining out. Consider cooking more meals at home to save money.',
            'potential_savings': eating_out * 0.5  # Assume 50% potential savings
        })
    
    # Suggestion 4: Entertainment expenses
    entertainment_expenses = expenses_data.get('Entertainment', {})
    entertainment_total = sum(entertainment_expenses.values())
    entertainment_pct = (entertainment_total / total_income * 100) if total_income > 0 else 0
    
    if entertainment_pct > 10:
        suggestions.append({
            'title': 'Review Entertainment Spending',
            'description': f'You\'re spending {entertainment_pct:.1f}% of your income on entertainment. Consider finding free or lower-cost alternatives for some activities.',
            'potential_savings': entertainment_total * 0.3  # Assume 30% potential savings
        })
    
    # Suggestion 5: Check subscription services
    streaming_services = expenses_data.get('Entertainment', {}).get('Streaming Services', 0)
    if streaming_services > 800:  # More than 800 NOK
        suggestions.append({
            'title': 'Review Subscription Services',
            'description': 'Your streaming service expenses are relatively high. Consider reviewing your subscriptions and canceling those you don\'t use regularly.',
            'potential_savings': streaming_services * 0.4  # Assume 40% potential savings
        })
    
    # Suggestion 6: Transportation costs
    transport_expenses = expenses_data.get('Transportation', {})
    transport_total = sum(transport_expenses.values())
    transport_pct = (transport_total / total_income * 100) if total_income > 0 else 0
    
    if transport_pct > 15:
        suggestions.append({
            'title': 'Optimize Transportation Costs',
            'description': f'You\'re spending {transport_pct:.1f}% of your income on transportation. Consider carpooling, public transport, or biking to reduce costs.',
            'potential_savings': transport_total * 0.2  # Assume 20% potential savings
        })
    
    # Always add a suggestion about emergency fund
    emergency_fund = expenses_data.get('Savings', {}).get('Emergency Fund', 0)
    if emergency_fund < total_income * 0.1:
        suggestions.append({
            'title': 'Build an Emergency Fund',
            'description': 'Financial experts recommend having 3-6 months of expenses saved in an emergency fund. Consider increasing your monthly contribution.',
            'potential_savings': -total_income * 0.1  # Negative because this is an increase in expenses
        })
    
    return suggestions

def export_to_excel(budget_data):
    """Create an Excel file with budget data and return it as a bytes object."""
    # Create a BytesIO object to store the Excel file
    output = io.BytesIO()
    
    # Get data
    income_data = budget_data['income']
    expenses_data = budget_data['expenses']
    
    total_income = get_total_income(income_data)
    total_expenses = get_total_expenses(expenses_data)
    savings = get_savings(total_income, total_expenses)
    savings_rate = (savings/total_income*100 if total_income > 0 else 0)
    
    # Create polars dataframes with strict=False to allow mixed types
    # Summary dataframe - use explicit float values to avoid type errors
    try:
        summary_df = pl.DataFrame({
            'Category': ['Total Income', 'Total Expenses', 'Savings', 'Savings Rate (%)'],
            'Amount': [
                float(total_income), 
                float(total_expenses), 
                float(savings), 
                float(savings_rate)
            ]
        })
    except TypeError:
        # Fallback with strict=False
        summary_df = pl.DataFrame({
            'Category': ['Total Income', 'Total Expenses', 'Savings', 'Savings Rate (%)'],
            'Amount': [
                total_income, 
                total_expenses, 
                savings, 
                savings_rate
            ]
        }, strict=False)
    
    # Income breakdown
    try:
        income_rows = [{'Category': source, 'Amount': float(amount)} for source, amount in income_data.items()]
        income_df = pl.DataFrame(income_rows)
    except TypeError:
        # Fallback with strict=False
        income_rows = [{'Category': source, 'Amount': amount} for source, amount in income_data.items()]
        income_df = pl.DataFrame(income_rows, strict=False)
    
    # Expense breakdown - flat view for Excel
    expense_rows = []
    for category, subcategories in expenses_data.items():
        category_total = sum(subcategories.values())
        expense_rows.append({
            'Main Category': category,
            'Subcategory': 'TOTAL',
            'Amount': float(category_total),
            'Percentage of Income': f'{(category_total/total_income*100 if total_income > 0 else 0):.1f}%'
        })
        
        for subcategory, amount in subcategories.items():
            if amount > 0:  # Only include subcategories with expenses
                expense_rows.append({
                    'Main Category': category,
                    'Subcategory': subcategory,
                    'Amount': float(amount),
                    'Percentage of Category': f'{(amount/category_total*100 if category_total > 0 else 0):.1f}%',
                    'Percentage of Income': f'{(amount/total_income*100 if total_income > 0 else 0):.1f}%'
                })
    
    try:
        expense_df = pl.DataFrame(expense_rows)
    except TypeError:
        # Fallback with strict=False
        expense_df = pl.DataFrame(expense_rows, strict=False)
    
    # Convert to pandas and write to Excel
    with pl.Config(tbl_hide_dataframe_shape=True, tbl_rows=-1):
        # Create a Pandas ExcelWriter object
        import pandas as pd
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write each dataframe to a different worksheet
            summary_df.to_pandas().to_excel(writer, sheet_name='Summary', index=False)
            income_df.to_pandas().to_excel(writer, sheet_name='Income', index=False)
            expense_df.to_pandas().to_excel(writer, sheet_name='Expenses', index=False)
            
            # Access the workbook and the worksheets
            workbook = writer.book
            
            # Format the summary sheet
            summary_sheet = writer.sheets['Summary']
            # Add currency formatting
            for row in range(2, 4):  # For Income, Expenses, and Savings
                cell = summary_sheet.cell(row=row, column=2)
                cell.number_format = '#,##0 "NOK"'
            
            # Format the income sheet
            income_sheet = writer.sheets['Income']
            for row in range(2, len(income_rows) + 2):
                cell = income_sheet.cell(row=row, column=2)
                cell.number_format = '#,##0 "NOK"'
            
            # Format the expenses sheet
            expense_sheet = writer.sheets['Expenses']
            for row in range(2, len(expense_rows) + 2):
                cell = expense_sheet.cell(row=row, column=3)
                cell.number_format = '#,##0 "NOK"'
    
    # Seek to the beginning of the stream
    output.seek(0)
    
    return output

# Main application
def main():
    # Get the user ID (this also handles authentication)
    user_id = get_user_id()
    
    # Display user info in the sidebar
    st.sidebar.title('User Info')
    st.sidebar.write(f'Logged in as: {st.session_state.username}')
    if st.sidebar.button('Logout'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.title('💰 Budget Analyzer')
    
    # Load budget data for the current user
    budget_data = load_budget_data(user_id)
    
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
        
        # NEW: Add Excel export button
        st.sidebar.markdown("---")
        st.sidebar.subheader("Export Data")
        
        excel_data = export_to_excel(budget_data)
        st.sidebar.download_button(
            label="📥 Download Budget as Excel",
            data=excel_data,
            file_name=f"budget_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download all your budget data as an Excel file with detailed summary and breakdowns"
        )
        
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
            
            # Pie chart for main categories
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
            
            # NEW: Add treemap visualization for all expense categories
            st.subheader('Detailed Expense Breakdown')
            
            # Prepare data for hierarchical visualizations
            # Convert to pandas format for visualization
            all_expenses = expense_df.to_pandas()
            
            # Create a hierarchical data structure for the treemap
            hierarchy_data = []
            
            # Add main categories first
            for category in main_categories.to_pandas().itertuples():
                hierarchy_data.append({
                    'id': category.Category,
                    'parent': '',
                    'value': category.Amount,
                    'name': category.Category,
                    'is_root': True  # Flag to identify root nodes
                })
            
            # Add subcategories
            for subcategory in expense_df.filter(pl.col('Category').str.contains(' - ')).to_pandas().itertuples():
                # Extract parent category and subcategory name
                parts = subcategory.Category.split(' - ')
                parent_category = parts[0]
                subcategory_name = parts[1]
                
                hierarchy_data.append({
                    'id': subcategory.Category,
                    'parent': parent_category,
                    'value': subcategory.Amount,
                    'name': subcategory_name,
                    'is_root': False  # Flag to identify non-root nodes
                })
            
            # Prepare the data for visualization
            ids = [item['id'] for item in hierarchy_data]
            labels = [item['name'] for item in hierarchy_data]
            parents = [item['parent'] for item in hierarchy_data]
            values = [item['value'] for item in hierarchy_data]
            
            # Create separate hover templates for main categories and subcategories
            hover_templates = []
            for item in hierarchy_data:
                if item['is_root']:
                    # For main categories
                    hover_templates.append(f"<b>{item['name']}</b><br>Amount: {item['value']:,.0f} NOK<br>% of total expenses")
                else:
                    # For subcategories
                    hover_templates.append(f"<b>{item['name']}</b><br>Amount: {item['value']:,.0f} NOK<br>% of {item['parent']}<br>% of total expenses")
            
            # Create treemap using go.Treemap
            fig3 = go.Figure(go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues='total',
                texttemplate='<b>%{label}</b><br>%{value:,.0f} NOK',
                marker=dict(colorscale='Blues'),
                hoverinfo='none',  # Use 'none' and rely on hovertemplate instead
                hovertemplate="""
<b>%{label}</b><br>
Amount: %{value:,.0f} NOK<br>
%{percentRoot:.1%} of total expenses<br>
%{percentParent:.1%} of %{parent}
<extra></extra>
"""
            ))
            
            fig3.update_layout(
                title='Hierarchical View of All Expenses',
                margin=dict(t=50, l=25, r=25, b=25)
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
            # NEW: Add a sunburst chart (radial hierarchical visualization)
            st.subheader('Expense Categories Visualization')
            
            # Use the same hierarchy data for the sunburst chart
            fig4 = go.Figure(go.Sunburst(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues='total',
                texttemplate='<b>%{label}</b>',
                marker=dict(colorscale='Viridis'),
                hoverinfo='none',  # Use 'none' and rely on hovertemplate instead
                hovertemplate="""
<b>%{label}</b><br>
Amount: %{value:,.0f} NOK<br>
%{percentRoot:.1%} of total expenses<br>
%{percentParent:.1%} of %{parent}
<extra></extra>
"""
            ))
            
            fig4.update_layout(
                title='Radial View of Expense Categories',
                margin=dict(t=50, l=0, r=0, b=10)
            )
            
            st.plotly_chart(fig4, use_container_width=True)
            
            # NEW: Income breakdown
            st.subheader('Income Breakdown')
            income_data = pl.DataFrame([
                {'Source': source, 'Amount': amount} 
                for source, amount in budget_data['income'].items()
                if amount > 0  # Only include sources with income
            ])
            
            if len(income_data) > 0:
                fig5 = px.pie(
                    income_data.to_pandas(), 
                    values='Amount', 
                    names='Source',
                    title='Income Sources Distribution',
                    color_discrete_sequence=px.colors.sequential.Greens
                )
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info('No income sources with values greater than zero.')
            
            # NEW: Expense vs Income by Category
            st.subheader('Budget Allocation')
            # Create a DataFrame with expense categories and their percentage of income
            expense_vs_income = main_categories.with_columns([
                (pl.col('Amount') / total_income * 100).round(1).alias('Percentage_of_Income')
            ])
            
            fig6 = px.bar(
                expense_vs_income.to_pandas(), 
                x='Category', 
                y='Percentage_of_Income',
                title='Expense Categories as Percentage of Income',
                color='Percentage_of_Income',
                color_continuous_scale='Reds',
                labels={'Percentage_of_Income': '% of Income'}
            )
            fig6.update_layout(yaxis_title='Percentage of Total Income (%)')
            st.plotly_chart(fig6, use_container_width=True)
            
            # NEW: Savings Suggestions
            st.header('💡 Savings Suggestions')
            
            suggestions = generate_savings_suggestions(budget_data)
            
            if suggestions:
                total_potential_savings = sum(max(0, s['potential_savings']) for s in suggestions)
                
                st.info(f"""
                Based on your current budget, we've identified potential savings of approximately 
                **{total_potential_savings:,.0f} {DEFAULT_CURRENCY}** per month.
                
                Here are some personalized suggestions to help you optimize your budget:
                """)
                
                for i, suggestion in enumerate(suggestions):
                    with st.expander(f"{i+1}. {suggestion['title']}"):
                        st.write(suggestion['description'])
                        if suggestion['potential_savings'] > 0:
                            st.write(f"**Potential monthly savings:** {suggestion['potential_savings']:,.0f} {DEFAULT_CURRENCY}")
                        elif suggestion['potential_savings'] < 0:
                            st.write(f"**Recommended additional expense:** {-suggestion['potential_savings']:,.0f} {DEFAULT_CURRENCY}")
            else:
                st.success("Your budget looks well-optimized! Keep up the good work.")
        else:
            st.info('No expense data to display. Please add expenses in the Edit Budget tab.')
    
    # Edit Budget Tab
    with tab2:
        st.header('Edit Your Budget')
        
        # Add helper text to explain the process
        st.info("""
        📝 **How to update your budget:**
        1. Modify any values in the income and expense fields below
        2. Click the 'Update Budget' button at the bottom to save your changes
        3. All changes are saved automatically to your personal budget file
        """)
        
        # Income Section
        st.subheader('Income')
        income_cols = st.columns(len(INCOME_CATEGORIES))
        
        for i, category in enumerate(INCOME_CATEGORIES):
            with income_cols[i]:
                budget_data['income'][category] = st.number_input(
                    f"{category} ({DEFAULT_CURRENCY})",
                    min_value=0,
                    value=budget_data['income'][category],
                    step=100,
                    key=f"income_{category}"
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
                            step=100,
                            key=f"expense_{category}_{subcategory}"
                        )
        
        # Save changes
        if st.button('Update Budget'):
            # Save the current budget data
            save_budget_data(budget_data, user_id)
            
            # Show success message with more details
            st.success('Budget updated successfully! Your changes have been saved.')
            
            # Show a summary of the updated budget
            total_income = get_total_income(budget_data['income'])
            total_expenses = get_total_expenses(budget_data['expenses'])
            savings = get_savings(total_income, total_expenses)
            
            # Display the updated summary
            st.info(f"""
            **Updated Budget Summary:**
            - **Total Income:** {total_income:,.0f} {DEFAULT_CURRENCY}
            - **Total Expenses:** {total_expenses:,.0f} {DEFAULT_CURRENCY}
            - **Savings:** {savings:,.0f} {DEFAULT_CURRENCY}
            - **Savings Rate:** {(savings/total_income*100 if total_income > 0 else 0):.1f}%
            """)
            
            # Rerun the app to ensure all data is fresh
            st.rerun()
    
    # Save/Load Tab
    with tab3:
        st.header('Save or Load Budget Presets')
        
        # Add helper text
        st.info("""
        💾 **Budget Presets:**
        - Save different versions of your budget as named presets
        - Load previously saved presets anytime
        - Reset to default values if needed
        
        Your current budget is always automatically saved to your user profile.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader('Save Current Budget as Preset')
            save_name = st.text_input('Preset Name', f'Budget_{datetime.now().strftime("%Y%m%d")}')
            
            if st.button('Save Budget Preset'):
                preset_dir = os.path.join('user_data', user_id)
                if not os.path.exists(preset_dir):
                    os.makedirs(preset_dir)
                
                file_path = os.path.join(preset_dir, f"{save_name}.json")
                with open(file_path, 'w') as f:
                    json.dump(budget_data, f, indent=4)
                st.success(f'Budget saved as preset: {save_name}!')
                
                # Show the list of available presets
                preset_files = [f for f in os.listdir(preset_dir) if f.endswith('.json')]
                if preset_files:
                    st.write('Your saved presets:')
                    for preset in preset_files:
                        st.write(f"- {preset.replace('.json', '')}")
        
        with col2:
            st.subheader('Load Saved Preset')
            preset_dir = os.path.join('user_data', user_id)
            
            if os.path.exists(preset_dir):
                preset_files = [f for f in os.listdir(preset_dir) if f.endswith('.json')]
                
                if preset_files:
                    selected_file = st.selectbox('Select a saved preset', preset_files)
                    
                    if st.button('Load Selected Preset'):
                        try:
                            with open(os.path.join(preset_dir, selected_file), 'r') as f:
                                loaded_data = json.load(f)
                            save_budget_data(loaded_data, user_id)
                            st.success(f'Budget loaded from preset: {selected_file}!')
                            st.rerun()
                        except Exception as e:
                            st.error(f'Error loading budget: {e}')
                else:
                    st.info('No saved presets found. Create a preset by saving your current budget.')
            else:
                st.info('No saved presets found. Create a preset by saving your current budget.')
        
        st.subheader('Reset to Default')
        st.warning('⚠️ This will reset all your budget values to the default amounts. This cannot be undone.')
        if st.button('Reset to Default Values'):
            default_budget = get_default_budget()
            save_budget_data(default_budget, user_id)
            st.success('Budget reset to default values!')
            st.rerun()

if __name__ == '__main__':
    main() 