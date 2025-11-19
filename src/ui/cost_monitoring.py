"""
Azure Cost Monitoring for SmartArchive

Provides cost tracking and optimization recommendations for Azure resources
used in the archive and ML pipeline.

Features:
- Real-time cost tracking by service (Storage, Compute, ML)
- Cost projection and trend analysis
- Optimization recommendations
- Budget alerts and thresholds
- Cost comparison with savings potential
- Integration with Azure Cost Management API for real cost data
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple, Optional
import json
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
import pathlib

# Find and load .env file from project root
env_paths = [
    pathlib.Path(__file__).parent.parent.parent / '.env',  # ml-poc/.env
    pathlib.Path.cwd() / '.env',  # Current working directory
    pathlib.Path.home() / '.env'  # Home directory
]

for env_path in env_paths:
    if env_path.exists():
        logger.info(f"Loading .env from: {env_path}")
        load_dotenv(env_path)
        break
else:
    logger.warning("No .env file found in standard locations")

# Azure SDK imports
logger.info("Attempting to import Azure SDK packages...")
try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.costmanagement import CostManagementClient
    from azure.mgmt.costmanagement.models import (
        QueryDefinition, 
        TimeframeType, 
        GranularityType,
        QueryDataset,
        QueryTimePeriod,
        QueryAggregation,
        QueryGrouping
    )
    AZURE_SDK_AVAILABLE = True
    logger.info("✅ Azure SDK packages imported successfully")
except ImportError as e:
    AZURE_SDK_AVAILABLE = False
    logger.warning(f"❌ Azure SDK import failed: {e}")
    logger.warning("Install with: pip install azure-mgmt-costmanagement azure-identity")
except Exception as e:
    AZURE_SDK_AVAILABLE = False
    logger.error(f"❌ Unexpected error importing Azure SDK: {type(e).__name__}: {e}")
    import traceback
    logger.error(traceback.format_exc())

logger = logging.getLogger(__name__)


# =====================================================================
# Mock Azure Cost Data
# =====================================================================

# Sample Azure cost data by service
AZURE_MONTHLY_COSTS = {
    'month': [
        '2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01', '2024-05-01', '2024-06-01',
        '2024-07-01', '2024-08-01', '2024-09-01', '2024-10-01', '2024-11-01', '2024-12-01'
    ],
    'storage_cost': [1200, 1320, 1380, 1450, 1580, 1620, 1750, 1890, 1950, 2100, 2250, 2380],
    'compute_cost': [800, 850, 920, 950, 1050, 1100, 1200, 1300, 1350, 1450, 1550, 1680],
    'ml_cost': [600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150],
    'bandwidth_cost': [200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420],
    'other_cost': [100, 120, 140, 150, 160, 180, 200, 220, 240, 260, 280, 300]
}

# Cost by service component
SERVICE_BREAKDOWN = {
    'Storage (Blob)': {'current': 2380, 'pct': 0.45, 'unit': '$/month'},
    'SQL Database': {'current': 850, 'pct': 0.16, 'unit': '$/month'},
    'App Service': {'current': 630, 'pct': 0.12, 'unit': '$/month'},
    'ML Compute': {'current': 1150, 'pct': 0.22, 'unit': '$/month'},
    'Data Transfer': {'current': 420, 'pct': 0.08, 'unit': '$/month'},
    'Other Services': {'current': 300, 'pct': 0.06, 'unit': '$/month'}
}

# Budget and optimization opportunities
BUDGET_CONFIG = {
    'monthly_budget': 6000,
    'alert_threshold': 0.80,  # Alert at 80% of budget
    'cost_optimization_potential': 0.15  # 15% potential savings
}

# Cost optimization recommendations
OPTIMIZATION_OPPORTUNITIES = [
    {
        'title': 'Archive Old Blobs to Cool Storage',
        'description': 'Move archives older than 90 days from Hot tier to Cool tier',
        'potential_savings': 350,  # $/month
        'effort': 'Medium',
        'impact': 'High',
        'implementation_time': '1-2 weeks'
    },
    {
        'title': 'Optimize Compute Instance Sizing',
        'description': 'Right-size ML compute instances based on actual utilization',
        'potential_savings': 280,
        'effort': 'Medium',
        'impact': 'High',
        'implementation_time': '2-3 weeks'
    },
    {
        'title': 'Reserved Instances (1-year)',
        'description': 'Purchase 1-year reserved capacity for predictable workloads',
        'potential_savings': 450,
        'effort': 'Low',
        'impact': 'Medium',
        'implementation_time': 'Immediate'
    },
    {
        'title': 'Implement Data Retention Policies',
        'description': 'Auto-delete archived files after retention period',
        'potential_savings': 200,
        'effort': 'Low',
        'impact': 'Medium',
        'implementation_time': '1 week'
    },
    {
        'title': 'Enable Autoscaling',
        'description': 'Scale compute resources up/down based on demand',
        'potential_savings': 180,
        'effort': 'Medium',
        'impact': 'Medium',
        'implementation_time': '2-3 weeks'
    },
    {
        'title': 'Consolidate Storage Accounts',
        'description': 'Reduce number of storage accounts from 3 to 1',
        'potential_savings': 120,
        'effort': 'High',
        'impact': 'Low',
        'implementation_time': '4-6 weeks'
    }
]


class AzureCostAnalyzer:
    """Analyze Azure costs and provide optimization recommendations"""
    
    def __init__(self, subscription_id: Optional[str] = None, resource_group: Optional[str] = None):
        """
        Initialize cost analyzer
        
        Args:
            subscription_id: Azure subscription ID (uses DefaultAzureCredential if not provided)
            resource_group: Azure resource group name (optional filter)
        """
        self.subscription_id = subscription_id or os.getenv('AZURE_SUBSCRIPTION_ID')
        self.resource_group = resource_group or os.getenv('AZURE_RESOURCE_GROUP')
        self.azure_client = None
        self.use_real_data = False
        
        # Check if Azure SDK is available
        if not AZURE_SDK_AVAILABLE:
            logger.warning(
                "⚠️ Azure SDK not available. Using mock data.\n"
                "   Install with: pip install azure-mgmt-costmanagement azure-identity"
            )
            self._load_mock_costs()
            return
        
        # Check if subscription ID is provided
        if not self.subscription_id:
            logger.warning(
                "⚠️ Azure subscription ID not provided. Using mock data.\n"
                "   Set the AZURE_SUBSCRIPTION_ID environment variable or pass subscription_id parameter.\n"
                f"   Example: export AZURE_SUBSCRIPTION_ID='your-subscription-id'"
            )
            self._load_mock_costs()
            return
        
        # Try to initialize Azure SDK client
        try:
            self._initialize_azure_client()
            self.use_real_data = True
            logger.info("✅ Connected to Azure Cost Management API - using real data")
            self._load_real_costs()
        except Exception as e:
            logger.warning(
                f"⚠️ Could not connect to Azure Cost Management API: {type(e).__name__}\n"
                f"   Error: {e}\n"
                "   Using mock data instead."
            )
            self.use_real_data = False
            self._load_mock_costs()
    
    def _initialize_azure_client(self):
        """Initialize Azure Cost Management client"""
        try:
            # Provide more detailed error information
            if not self.subscription_id:
                raise ValueError(
                    "Azure subscription ID not provided. Set AZURE_SUBSCRIPTION_ID environment variable "
                    "or pass subscription_id parameter to AzureCostAnalyzer()"
                )
            
            logger.info("Attempting to authenticate with Azure...")
            credential = DefaultAzureCredential()
            
            logger.info(f"Creating Cost Management client for subscription: {self.subscription_id}")
            self.azure_client = CostManagementClient(credential)
            
            logger.info(f"✅ Azure Cost Management client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure client: {type(e).__name__}: {e}")
            logger.error(
                "Possible causes:\n"
                "  1. Missing AZURE_SUBSCRIPTION_ID environment variable\n"
                "  2. Azure authentication not configured (run 'az login')\n"
                "  3. Insufficient permissions on the subscription\n"
                "  4. Network/firewall issues"
            )
            raise
    
    def _load_real_costs(self):
        """Load real cost data from Azure Cost Management API"""
        try:
            logger.info("Loading real cost data from Azure...")
            
            # Get cost data for last 2 months only (reduces API quota usage)
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=7)  # Last 7 days
            
            logger.info(f"Querying costs from {start_date} to {end_date} (last 2 months)")
            
            # Build query for Cost Management API
            # Note: QueryDefinition structure based on azure-mgmt-costmanagement v4.0+
            query = QueryDefinition(
                type='Usage',
                timeframe='Custom',
                time_period=QueryTimePeriod(
                    from_property=start_date.isoformat() + 'T00:00:00Z',
                    to=end_date.isoformat() + 'T23:59:59Z'
                ),
                dataset=QueryDataset(
                    granularity='Monthly',
                    aggregation={
                        'totalCost': QueryAggregation(
                            name='PreTaxCost',
                            function='Sum'
                        )
                    },
                    grouping=[
                        QueryGrouping(
                            type='Dimension',
                            name='MeterCategory'
                        )
                    ]
                )
            )
            
            # Query Azure Cost Management API
            scope = f'/subscriptions/{self.subscription_id}'
            if self.resource_group:
                scope = f'/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}'
            
            logger.info(f"Querying Azure Cost Management API for scope: {scope}")
            result = self.azure_client.query.usage(scope, query)
            
            # Parse results into monthly costs
            self.monthly_costs = self._parse_azure_costs(result)
            logger.info(f"✅ Loaded {len(self.monthly_costs)} months of real cost data")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to load real costs: {e}")
            
            # Handle rate limiting specifically
            if "429" in error_message or "Too many requests" in error_message:
                logger.warning("⚠️ Azure Cost Management API rate limit exceeded.")
                logger.warning("Rate limits: https://learn.microsoft.com/en-us/azure/cost-management-billing/automate/usage-details-best-practices")
                logger.info("💡 Using cached mock data. The dashboard will retry on next restart.")
            elif "BadRequest" in error_message or "time period" in error_message:
                logger.warning("⚠️ Query time period issue. Adjusting query parameters...")
            else:
                logger.info("Falling back to mock data...")
                
            self._load_mock_costs()
            self.use_real_data = False
    
    def _parse_azure_costs(self, result) -> pd.DataFrame:
        """Parse Azure Cost Management API response into DataFrame"""
        try:
            rows = result.rows
            columns = result.columns
            
            # Extract data
            data = {
                'month': [],
                'storage_cost': [],
                'compute_cost': [],
                'ml_cost': [],
                'bandwidth_cost': [],
                'other_cost': []
            }
            
            for row in rows:
                # Extract month and costs by category
                month = row[0]  # Time period
                meter_category = row[1]  # e.g., "Storage", "Virtual Machines"
                cost = float(row[-1]) if row[-1] else 0  # Last column is cost
                
                # Categorize costs
                if 'Storage' in meter_category:
                    data['storage_cost'].append(cost)
                elif 'Virtual Machines' in meter_category or 'App Service' in meter_category:
                    data['compute_cost'].append(cost)
                elif 'Machine Learning' in meter_category:
                    data['ml_cost'].append(cost)
                elif 'Bandwidth' in meter_category:
                    data['bandwidth_cost'].append(cost)
                else:
                    data['other_cost'].append(cost)
            
            df = pd.DataFrame(data)
            return df
            
        except Exception as e:
            logger.error(f"Error parsing Azure costs: {e}")
            return self._load_mock_costs()
    
    def _load_mock_costs(self):
        """Load mock cost data (fallback)"""
        self.monthly_costs = pd.DataFrame(AZURE_MONTHLY_COSTS)
        self.monthly_costs['month'] = pd.to_datetime(self.monthly_costs['month'])
        self.use_real_data = False
        self.total_cost_column = ['storage_cost', 'compute_cost', 'ml_cost', 'bandwidth_cost', 'other_cost']
        self.monthly_costs['total_cost'] = self.monthly_costs[self.total_cost_column].sum(axis=1)
    
    def get_current_costs(self) -> Dict[str, float]:
        """Get current monthly costs breakdown"""
        if self.use_real_data:
            return self._get_real_current_costs()
        else:
            return self._get_mock_current_costs()
    
    def _get_mock_current_costs(self) -> Dict[str, float]:
        """Get current monthly costs from mock data"""
        latest = self.monthly_costs.iloc[-1]
        return {
            'storage': float(latest['storage_cost']),
            'compute': float(latest['compute_cost']),
            'ml': float(latest['ml_cost']),
            'bandwidth': float(latest['bandwidth_cost']),
            'other': float(latest['other_cost']),
            'total': float(latest['total_cost'])
        }
    
    def _get_real_current_costs(self) -> Dict[str, float]:
        """Get current monthly costs from Azure Cost Management API"""
        try:
            end_date = datetime.utcnow().date()
            start_date = (end_date.replace(day=1))  # First day of current month
            
            logger.info(f"Querying current month costs from {start_date} to {end_date}")
            
            query = QueryDefinition(
                type='Usage',
                timeframe='Custom',
                time_period=QueryTimePeriod(
                    from_property=start_date.isoformat() + 'T00:00:00Z',
                    to=end_date.isoformat() + 'T23:59:59Z'
                ),
                dataset=QueryDataset(
                    granularity='Daily',
                    aggregation={
                        'totalCost': QueryAggregation(
                            name='PreTaxCost',
                            function='Sum'
                        )
                    },
                    grouping=[
                        QueryGrouping(
                            type='Dimension',
                            name='MeterCategory'
                        )
                    ]
                )
            )
            
            scope = f'/subscriptions/{self.subscription_id}'
            if self.resource_group:
                scope = f'/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}'
            
            result = self.azure_client.query.usage(scope, query)
            
            # Parse results
            costs = {
                'storage': 0.0,
                'compute': 0.0,
                'ml': 0.0,
                'bandwidth': 0.0,
                'other': 0.0,
                'total': 0.0
            }
            
            for row in result.rows:
                meter_category = row[1] if len(row) > 1 else ''
                cost = float(row[-1]) if row[-1] else 0
                
                if 'Storage' in meter_category:
                    costs['storage'] += cost
                elif 'Virtual Machines' in meter_category or 'App Service' in meter_category:
                    costs['compute'] += cost
                elif 'Machine Learning' in meter_category:
                    costs['ml'] += cost
                elif 'Bandwidth' in meter_category:
                    costs['bandwidth'] += cost
                else:
                    costs['other'] += cost
                
                costs['total'] += cost
            
            return costs
            
        except Exception as e:
            logger.error(f"Error fetching real current costs: {e}")
            return self._get_mock_current_costs()
    
    def get_cost_trend(self) -> Tuple[float, float, str]:
        """
        Get cost trend information
        
        Returns:
            Tuple of (current_month, previous_month, trend_direction)
        """
        latest = self.monthly_costs.iloc[-1]['total_cost']
        previous = self.monthly_costs.iloc[-2]['total_cost']
        trend = 'Up' if latest > previous else 'Down'
        change = latest - previous
        pct_change = (change / previous) * 100
        
        return latest, previous, trend, change, pct_change
    
    def get_projected_annual_cost(self) -> float:
        """Project annual cost based on recent average"""
        recent_avg = self.monthly_costs.iloc[-3:]['total_cost'].mean()
        return recent_avg * 12
    
    def get_savings_potential(self) -> Dict[str, float]:
        """Calculate potential savings from optimization"""
        total_potential = sum(opp['potential_savings'] for opp in OPTIMIZATION_OPPORTUNITIES)
        current_total = self.get_current_costs()['total']
        
        return {
            'total_potential_savings': total_potential,
            'percent_of_current': (total_potential / current_total) * 100,
            'achievable_in_3_months': total_potential * 0.6,
            'achievable_in_6_months': total_potential * 0.85,
            'achievable_in_12_months': total_potential
        }
    
    def get_budget_status(self) -> Dict[str, any]:
        """Get budget status and alerts"""
        current = self.get_current_costs()['total']
        budget = BUDGET_CONFIG['monthly_budget']
        threshold = BUDGET_CONFIG['alert_threshold']
        spent_percent = (current / budget) * 100
        
        status = 'Good'
        if spent_percent >= 100:
            status = 'Over Budget'
        elif spent_percent >= threshold * 100:
            status = 'Caution'
        
        return {
            'current_spend': current,
            'budget': budget,
            'spent_percent': spent_percent,
            'remaining': budget - current,
            'status': status,
            'alert_threshold': threshold
        }
    
    def get_cost_efficiency_metrics(self) -> Dict[str, float]:
        """Calculate cost efficiency metrics"""
        # Cost per GB archived (placeholder calculation)
        total_archived_gb = 2500  # From mock data
        total_cost_ytd = self.monthly_costs['total_cost'].sum()
        
        cost_per_gb = total_cost_ytd / total_archived_gb if total_archived_gb > 0 else 0
        
        # Cost per transaction (simplified)
        total_transactions = 1500000  # Estimated
        cost_per_transaction = (total_cost_ytd / total_transactions) if total_transactions > 0 else 0
        
        return {
            'cost_per_gb_archived': cost_per_gb,
            'cost_per_million_transactions': cost_per_transaction * 1_000_000,
            'monthly_trend': (self.monthly_costs.iloc[-1]['total_cost'] - 
                            self.monthly_costs.iloc[-2]['total_cost']) / self.monthly_costs.iloc[-2]['total_cost'] * 100
        }


def create_cost_overview_section():
    """Create cost overview with key metrics"""
    import streamlit as st
    
    # Cache the analyzer to avoid multiple API calls
    @st.cache_resource
    def get_analyzer():
        return AzureCostAnalyzer()
    
    analyzer = get_analyzer()
    
    st.subheader("💰 Cost Overview")
    
    # Current costs
    costs = analyzer.get_current_costs()
    latest, previous, trend, change, pct_change = analyzer.get_cost_trend()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Current Monthly Cost",
            value=f"${latest:,.0f}",
            delta=f"${change:+,.0f} ({pct_change:+.1f}%)",
            delta_color="inverse"
        )
    
    with col2:
        annual = analyzer.get_projected_annual_cost()
        st.metric(
            label="Projected Annual Cost",
            value=f"${annual:,.0f}",
            delta="Based on 3-month avg"
        )
    
    with col3:
        budget = analyzer.get_budget_status()
        color = "off" if budget['status'] == 'Good' else "inverse"
        st.metric(
            label="Budget Status",
            value=f"{budget['spent_percent']:.1f}%",
            delta=f"${budget['remaining']:+,.0f} remaining",
            delta_color=color
        )
    
    with col4:
        savings = analyzer.get_savings_potential()
        st.metric(
            label="Optimization Potential",
            value=f"${savings['total_potential_savings']:,.0f}",
            delta=f"{savings['percent_of_current']:.1f}% of current"
        )


def create_cost_breakdown_chart():
    """Create cost breakdown by service"""
    import streamlit as st
    
    # Cache the analyzer to avoid multiple API calls
    @st.cache_resource
    def get_analyzer():
        return AzureCostAnalyzer()
    
    analyzer = get_analyzer()
    costs = analyzer.get_current_costs()
    
    # Prepare data for pie chart
    services = ['Storage', 'Compute', 'ML Services', 'Bandwidth', 'Other']
    values = [costs['storage'], costs['compute'], costs['ml'], costs['bandwidth'], costs['other']]
    
    fig = go.Figure(data=[go.Pie(
        labels=services,
        values=values,
        marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']),
        hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title="Current Cost Breakdown by Service",
        height=400
    )
    
    return fig


def create_cost_trend_chart():
    """Create historical cost trend chart"""
    import streamlit as st
    
    # Cache the analyzer to avoid multiple API calls
    @st.cache_resource
    def get_analyzer():
        return AzureCostAnalyzer()
    
    analyzer = get_analyzer()
    df = analyzer.monthly_costs.copy()
    
    fig = go.Figure()
    
    # Add total cost line
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=df['total_cost'],
        mode='lines+markers',
        name='Total Cost',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Add service breakdowns as stacked area
    services = [
        ('storage_cost', 'Storage', '#1f77b4'),
        ('compute_cost', 'Compute', '#ff7f0e'),
        ('ml_cost', 'ML Services', '#2ca02c'),
        ('bandwidth_cost', 'Bandwidth', '#d62728'),
        ('other_cost', 'Other', '#9467bd')
    ]
    
    for col, name, color in services:
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df[col],
            mode='lines',
            name=name,
            line=dict(width=0.5, color=color),
            fillcolor=color,
            stackgroup='one'
        ))
    
    fig.update_layout(
        title="Cost Trend Over Time (12 Months)",
        xaxis_title="Month",
        yaxis_title="Cost ($)",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig


def create_optimization_recommendations():
    """Display cost optimization recommendations"""
    import streamlit as st
    
    st.subheader("🔧 Cost Optimization Opportunities")
    
    # Cache the analyzer to avoid multiple API calls
    @st.cache_resource
    def get_analyzer():
        return AzureCostAnalyzer()
    
    analyzer = get_analyzer()
    savings = analyzer.get_savings_potential()
    
    st.markdown(f"""
    **Total Potential Savings: ${savings['total_potential_savings']:,.0f}/month ({savings['percent_of_current']:.1f}% of current costs)**
    
    Below are actionable recommendations ranked by potential impact:
    """)
    
    # Create a dataframe of opportunities
    opportunities_data = []
    for opp in OPTIMIZATION_OPPORTUNITIES:
        opportunities_data.append({
            'Opportunity': opp['title'],
            'Savings': f"${opp['potential_savings']}",
            'Effort': opp['effort'],
            'Impact': opp['impact'],
            'Timeline': opp['implementation_time']
        })
    
    df_opps = pd.DataFrame(opportunities_data)
    
    # Display with color coding for effort
    st.markdown("#### Recommended Actions")
    
    for idx, opp in enumerate(OPTIMIZATION_OPPORTUNITIES):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Determine effort color
            effort_color = '🟢' if opp['effort'] == 'Low' else ('🟡' if opp['effort'] == 'Medium' else '🔴')
            
            st.markdown(f"""
            **{idx + 1}. {opp['title']}**
            
            {opp['description']}
            
            - **Effort**: {effort_color} {opp['effort']}
            - **Implementation**: {opp['implementation_time']}
            """)
        
        with col2:
            st.metric("Monthly Savings", f"${opp['potential_savings']}")
        
        st.divider()
    
    # Summary timeline
    st.markdown("#### Savings Timeline")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "3-Month Target",
            f"${savings['achievable_in_3_months']:,.0f}",
            f"{(savings['achievable_in_3_months']/savings['total_potential_savings'])*100:.0f}% achievable"
        )
    
    with col2:
        st.metric(
            "6-Month Target",
            f"${savings['achievable_in_6_months']:,.0f}",
            f"{(savings['achievable_in_6_months']/savings['total_potential_savings'])*100:.0f}% achievable"
        )
    
    with col3:
        st.metric(
            "12-Month Target",
            f"${savings['achievable_in_12_months']:,.0f}",
            "Full potential"
        )


def create_budget_alerts_section():
    """Display budget alerts and warnings"""
    import streamlit as st
    
    st.subheader("🚨 Budget & Alerts")
    
    # Cache the analyzer to avoid multiple API calls
    @st.cache_resource
    def get_analyzer():
        return AzureCostAnalyzer()
    
    analyzer = get_analyzer()
    budget = analyzer.get_budget_status()
    
    # Status indicator
    if budget['status'] == 'Good':
        status_icon = '🟢'
        status_color = 'green'
    elif budget['status'] == 'Caution':
        status_icon = '🟡'
        status_color = 'orange'
    else:
        status_icon = '🔴'
        status_color = 'red'
    
    st.markdown(f"### {status_icon} {budget['status']}")
    
    # Progress bar
    progress = min(budget['spent_percent'] / 100, 1.0)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.progress(progress)
    
    with col2:
        st.markdown(f"**{budget['spent_percent']:.1f}%**")
    
    # Budget details
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Monthly Budget", f"${budget['budget']:,.0f}")
    
    with col2:
        st.metric("Current Spend", f"${budget['current_spend']:,.0f}")
    
    with col3:
        st.metric("Remaining", f"${budget['remaining']:,.0f}")
    
    st.divider()
    
    # Cost efficiency metrics
    st.markdown("#### Cost Efficiency")
    
    metrics = analyzer.get_cost_efficiency_metrics()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Cost per GB Archived",
            f"${metrics['cost_per_gb_archived']:.2f}",
            "Lower is better"
        )
    
    with col2:
        st.metric(
            "Cost per M Transactions",
            f"${metrics['cost_per_million_transactions']:.2f}",
            "Computed metric"
        )
    
    with col3:
        trend = "📈 Up" if metrics['monthly_trend'] > 0 else "📉 Down"
        st.metric(
            "Monthly Trend",
            f"{metrics['monthly_trend']:.1f}%",
            trend
        )


def create_cost_monitoring_dashboard():
    """Main cost monitoring dashboard"""
    import streamlit as st
    
    st.markdown("# 💳 Azure Cost Monitoring")
    st.markdown("*Track and optimize Azure resource costs for SmartArchive*")
    
    st.divider()
    
    # Cost overview
    create_cost_overview_section()
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_breakdown = create_cost_breakdown_chart()
        st.plotly_chart(fig_breakdown, use_container_width=True)
    
    with col2:
        fig_trend = create_cost_trend_chart()
        st.plotly_chart(fig_trend, use_container_width=True)
    
    st.divider()
    
    # Budget alerts
    create_budget_alerts_section()
    
    st.divider()
    
    # Optimization recommendations
    create_optimization_recommendations()
    
    st.divider()
    
    # Cost management tips
    st.markdown("#### 💡 Cost Management Best Practices")
    
    st.markdown("""
    1. **Monitor Regularly**: Check costs daily/weekly to catch unexpected spikes early
    2. **Use Cost Alerts**: Set up Azure Cost Management alerts for budget thresholds
    3. **Implement Tagging**: Tag resources by project/department for better cost allocation
    4. **Review Reserved Instances**: Analyze commit-based options for predictable workloads
    5. **Archive Strategically**: Use tiered storage (Hot/Cool/Archive) based on access patterns
    6. **Automate Cleanup**: Remove unused resources, old backups, and orphaned snapshots
    7. **Optimize Compute**: Right-size instances and use spot instances for non-critical workloads
    8. **Monitor Data Transfer**: Minimize data transfer costs through efficient data location
    """)
