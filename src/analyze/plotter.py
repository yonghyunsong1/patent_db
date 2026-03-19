import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

def generate_company_dashboard(csv_path, output_dir):
    # 1. Load the processed data
    df = pd.read_csv(csv_path)
    if df.empty:
        return
        
    company_name = df['Target_Company'].iloc[0].upper()
    safe_name = os.path.basename(csv_path).replace("_diligence_data.csv", "")
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle(f"IP Portfolio Dashboard: {company_name}", fontsize=20, fontweight='bold', y=1.05)

    # Master Color Map so all charts match perfectly
    color_map = {
        'Enforceable (Granted)': '#2ca02c',       # Green
        'Pipeline (Active/Pending)': '#1f77b4',   # Blue
        'Abandoned (Wastage)': '#d62728',         # Red
        'PCT (Intl. Placeholder)': '#9467bd',     # Purple
        'Provisional (Placeholder)': '#ff7f0e'    # Orange
    }

    # ==========================================
    # PANEL 1: Portfolio Health (Donut Chart)
    # ==========================================
    status_counts = df['Business_Category'].value_counts()
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
                
    axes[0].set_title("Portfolio Health (Status)", fontsize=14, fontweight='bold')

    # ==========================================
    # PANEL 2: R&D Velocity (Stacked Bar by Status)
    # ==========================================
    df['Filing_Date'] = pd.to_datetime(df['Filing_Date'], errors='coerce')
    df['Filing_Year'] = df['Filing_Date'].dt.year

    if not df['Filing_Year'].dropna().empty:
        # Create a pivot table: Rows = Years, Columns = Business Categories, Values = Counts
        yearly_stats = df.groupby(['Filing_Year', 'Business_Category']).size().unstack(fill_value=0)
        
        # Ensure the colors map correctly to whatever columns actually exist in this specific company's data
        bar_colors = [color_map.get(col, '#7f7f7f') for col in yearly_stats.columns]
        
        # Plot the stacked bar chart directly from Pandas
        yearly_stats.plot(kind='bar', stacked=True, ax=axes[1], color=bar_colors, edgecolor='white', width=0.8)
        
        axes[1].set_title("R&D Velocity (Filings per Year)", fontsize=14, fontweight='bold')
        axes[1].set_ylabel("Number of Applications")
        axes[1].set_xlabel("Filing Year")
        axes[1].tick_params(axis='x', rotation=45)
        
        # Format the legend so it doesn't block the data
        axes[1].legend(title="", fontsize=9, loc='upper left', framealpha=0.9)
    else:
        axes[1].text(0.5, 0.5, "No Date Data Available", ha='center', va='center')
        axes[1].set_title("R&D Velocity")

    # ==========================================
    # PANEL 3: Outside Counsel (Law Firms)
    # ==========================================
    firm_counts = df['Law_Firm'].value_counts().head(5)
    
    # Using hue to satisfy the new Seaborn requirements
    sns.barplot(y=firm_counts.index, x=firm_counts.values, ax=axes[2], 
                hue=firm_counts.index, palette="viridis", legend=False)
                
    axes[2].set_title("Top Outside Counsel (Law Firms)", fontsize=14, fontweight='bold')
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
    
    output_path = f"{output_dir}/{safe_name}_dashboard.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close() 
    
    print(f"📊 Generated Graphic: {output_path}")

def main():
    # Bulletproof Pathing
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    csv_dir = os.path.join(root_dir, "data", "processed")
    output_dir = os.path.join(root_dir, "outputs", "figures")
    os.makedirs(output_dir, exist_ok=True)

    csv_files = glob.glob(os.path.join(csv_dir, "*_diligence_data.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found in {csv_dir}. Run data_processor.py first.")
        return

    print("Generating visual dashboards...")
    for file in csv_files:
        generate_company_dashboard(file, output_dir)
        
    print(f"\n✅ All graphics successfully generated in '{output_dir}'!")

if __name__ == "__main__":
    main()