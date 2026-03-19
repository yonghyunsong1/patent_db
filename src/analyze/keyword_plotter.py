import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

def clean_in_house_counsel(row):
    """Checks if the law firm is actually just the company's internal IP department."""
    firm = str(row['Law_Firm']).upper()
    comp = str(row['Company']).upper()
    
    # If the company name is known, check if its first main word appears in the law firm address
    if comp != 'UNKNOWN' and len(comp.split()) > 0:
        first_word = comp.split()[0].replace(",", "").replace(".", "")
        if len(first_word) > 2 and first_word in firm:
            return "IN-HOUSE COUNSEL"
            
    return row['Law_Firm']

def generate_landscape_dashboard(csv_path, output_dir):
    df = pd.read_csv(csv_path)
    if df.empty:
        return
        
    keyword = str(df['Keyword'].iloc[0]).title()
    safe_name = os.path.basename(csv_path).replace("_landscape.csv", "")
    
    # Apply the in-house counsel cleanup
    df['Law_Firm'] = df.apply(clean_in_house_counsel, axis=1)
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(22, 6))
    fig.suptitle(f"Technology Landscape: '{keyword}'", fontsize=20, fontweight='bold', y=1.05)

# ==========================================
    # PANEL 1: Top Companies in this Space
    # ==========================================
    # Filter out 'Unknown' companies
    comp_df = df[df['Company'] != 'Unknown']
    
    if not comp_df.empty:
        company_counts = comp_df['Company'].value_counts().head(5)
        
        sns.barplot(y=company_counts.index, x=company_counts.values, ax=axes[0], 
                    hue=company_counts.index, palette="Blues_r", legend=False)
                    
        axes[0].set_title("Top Assignees (Companies)", fontsize=14, fontweight='bold')
        axes[0].set_xlabel("Number of Patents")
        
        # Clean up long company names for the y-axis
        axes[0].set_yticks(axes[0].get_yticks())
        comp_labels = [label.get_text()[:25] + '...' if len(label.get_text()) > 25 else label.get_text() 
                       for label in axes[0].get_yticklabels()]
        axes[0].set_yticklabels(comp_labels)
    else:
        axes[0].text(0.5, 0.5, "No Assignee Data Found in USPTO Record", ha='center', va='center')
        axes[0].set_title("Top Assignees (Companies)", fontsize=14, fontweight='bold')
        axes[0].axis('off') # Hide gridlines if empty
        
    # ==========================================
    # PANEL 2: Innovation Velocity (Timeline)
    # ==========================================
    color_map = {
        'Enforceable (Granted)': '#2ca02c', 'Pipeline (Active/Pending)': '#1f77b4',
        'Abandoned (Wastage)': '#d62728', 'PCT (Intl. Placeholder)': '#9467bd',
        'Provisional (Placeholder)': '#ff7f0e'
    }

    df['Filing_Date'] = pd.to_datetime(df['Filing_Date'], errors='coerce')
    df['Filing_Year'] = df['Filing_Date'].dt.year

    if not df['Filing_Year'].dropna().empty:
        yearly_stats = df.groupby(['Filing_Year', 'Lifecycle_Category']).size().unstack(fill_value=0)
        bar_colors = [color_map.get(col, '#7f7f7f') for col in yearly_stats.columns]
        
        yearly_stats.plot(kind='bar', stacked=True, ax=axes[1], color=bar_colors, edgecolor='white', width=0.8)
        
        axes[1].set_title("Innovation Velocity (Filings per Year)", fontsize=14, fontweight='bold')
        axes[1].set_ylabel("Number of Applications")
        axes[1].set_xlabel("Filing Year")
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].legend(title="", fontsize=9, loc='upper left', framealpha=0.9)
    else:
        axes[1].text(0.5, 0.5, "No Date Data Available", ha='center', va='center')
        axes[1].set_title("Innovation Velocity")

    # ==========================================
    # PANEL 3: Top Prosecuting Law Firms
    # ==========================================
    firm_counts = df['Law_Firm'].value_counts().head(5)
    
    # Highlight In-House Counsel in a different color to make it obvious
    firm_palette = ["#ff7f0e" if "IN-HOUSE" in firm else "#2ca02c" for firm in firm_counts.index]
    
    sns.barplot(y=firm_counts.index, x=firm_counts.values, ax=axes[2], 
                hue=firm_counts.index, palette=firm_palette, legend=False)
                
    axes[2].set_title("Top Prosecuting Law Firms", fontsize=14, fontweight='bold')
    axes[2].set_xlabel("Number of Applications Handled")
    
    # Clean up long law firm names for the y-axis
    axes[2].set_yticks(axes[2].get_yticks())
    firm_labels = [label.get_text()[:30] + '...' if len(label.get_text()) > 30 else label.get_text() 
                   for label in axes[2].get_yticklabels()]
    axes[2].set_yticklabels(firm_labels)

    # ==========================================
    # Finish and Save
    # ==========================================
    plt.tight_layout()
    plt.subplots_adjust(top=0.85, wspace=0.4) # wspace adds horizontal breathing room between charts
    
    output_path = os.path.join(output_dir, f"{safe_name}_dashboard.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close() 
    
    print(f"📊 Generated Graphic: {os.path.basename(output_path)}")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    csv_dir = os.path.join(root_dir, "data", "processed")
    output_dir = os.path.join(root_dir, "outputs", "figures")
    os.makedirs(output_dir, exist_ok=True)

    csv_files = glob.glob(os.path.join(csv_dir, "tech_*_landscape.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found.")
        return

    print("Generating visual dashboards...\n")
    for file in csv_files:
        generate_landscape_dashboard(file, output_dir)
        
    print(f"\n✅ All graphics successfully generated in '{output_dir}'!")

if __name__ == "__main__":
    main()