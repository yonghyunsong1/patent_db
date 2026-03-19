import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

def generate_landscape_dashboard(csv_path, output_dir):
    # 1. Load the processed data
    df = pd.read_csv(csv_path)
    if df.empty:
        return
        
    # Extract the target info for the titles
    keyword = str(df['Keyword'].iloc[0]).title()
    tech_category = str(df['Technology_Category'].iloc[0]).title()
    
    # Clean up the filename for saving
    safe_name = os.path.basename(csv_path).replace("_landscape.csv", "")
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    # Updated main title for Technology Landscaping
    fig.suptitle(f"Technology Landscape: '{keyword}'\nCategory: {tech_category}", 
                 fontsize=20, fontweight='bold', y=1.08)

    # Master Color Map so all charts match perfectly
    color_map = {
        'Enforceable (Granted)': '#2ca02c',       # Green
        'Pipeline (Active/Pending)': '#1f77b4',   # Blue
        'Abandoned (Wastage)': '#d62728',         # Red
        'PCT (Intl. Placeholder)': '#9467bd',     # Purple
        'Provisional (Placeholder)': '#ff7f0e'    # Orange
    }

    # ==========================================
    # PANEL 1: Technology Maturity (Donut Chart)
    # ==========================================
    status_counts = df['Lifecycle_Category'].value_counts()
    colors = [color_map.get(cat, '#7f7f7f') for cat in status_counts.index]

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f'{pct:.1f}%\n({val})'
        return my_autopct

    axes[0].pie(status_counts, labels=status_counts.index, 
                autopct=make_autopct(status_counts), 
                startangle=140, colors=colors, 
                wedgeprops=dict(width=0.4, edgecolor='w'),
                textprops={'fontsize': 10, 'fontweight': 'bold'})
                
    axes[0].set_title("Technology Maturity (Status)", fontsize=14, fontweight='bold')

    # ==========================================
    # PANEL 2: Innovation Velocity (Stacked Bar)
    # ==========================================
    df['Filing_Date'] = pd.to_datetime(df['Filing_Date'], errors='coerce')
    df['Filing_Year'] = df['Filing_Date'].dt.year

    if not df['Filing_Year'].dropna().empty:
        # Create a pivot table: Rows = Years, Columns = Lifecycle Categories, Values = Counts
        yearly_stats = df.groupby(['Filing_Year', 'Lifecycle_Category']).size().unstack(fill_value=0)
        
        # Ensure the colors map correctly to whatever columns actually exist in this specific dataset
        bar_colors = [color_map.get(col, '#7f7f7f') for col in yearly_stats.columns]
        
        # Plot the stacked bar chart directly from Pandas
        yearly_stats.plot(kind='bar', stacked=True, ax=axes[1], color=bar_colors, edgecolor='white', width=0.8)
        
        axes[1].set_title("Innovation Velocity (Filings per Year)", fontsize=14, fontweight='bold')
        axes[1].set_ylabel("Number of Applications")
        axes[1].set_xlabel("Filing Year")
        axes[1].tick_params(axis='x', rotation=45)
        
        # Format the legend so it doesn't block the data
        axes[1].legend(title="", fontsize=9, loc='upper left', framealpha=0.9)
    else:
        axes[1].text(0.5, 0.5, "No Date Data Available", ha='center', va='center')
        axes[1].set_title("Innovation Velocity")

    # ==========================================
    # PANEL 3: Top Prosecuting Law Firms
    # ==========================================
    firm_counts = df['Law_Firm'].value_counts().head(5)
    
    # Using hue to satisfy the new Seaborn requirements
    sns.barplot(y=firm_counts.index, x=firm_counts.values, ax=axes[2], 
                hue=firm_counts.index, palette="viridis", legend=False)
                
    axes[2].set_title("Top Prosecuting Law Firms in Space", fontsize=14, fontweight='bold')
    axes[2].set_xlabel("Number of Applications Handled")
    axes[2].set_ylabel("")
    
    # Fix the Matplotlib formatting warnings and clean up long names
    axes[2].set_yticks(axes[2].get_yticks())
    labels = [label.get_text()[:30] + '...' if len(label.get_text()) > 30 else label.get_text() 
              for label in axes[2].get_yticklabels()]
    axes[2].set_yticklabels(labels)

    # ==========================================
    # Finish and Save
    # ==========================================
    plt.tight_layout()
    
    # Add a little extra padding at the top so the main title doesn't overlap
    plt.subplots_adjust(top=0.85)
    
    output_path = os.path.join(output_dir, f"{safe_name}_dashboard.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close() 
    
    print(f"📊 Generated Graphic: {os.path.basename(output_path)}")

def main():
    # Bulletproof Pathing
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    csv_dir = os.path.join(root_dir, "data", "processed")
    output_dir = os.path.join(root_dir, "outputs", "figures")
    os.makedirs(output_dir, exist_ok=True)

    # Note: Updated glob to catch the 'tech_*_landscape.csv' files
    csv_files = glob.glob(os.path.join(csv_dir, "tech_*_landscape.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found in {csv_dir}. Run your processing script first.")
        return

    print("Generating visual dashboards...\n")
    for file in csv_files:
        generate_landscape_dashboard(file, output_dir)
        
    print(f"\n✅ All graphics successfully generated in '{output_dir}'!")

if __name__ == "__main__":
    main()