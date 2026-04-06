import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

def clean_in_house_counsel(row):
    """Checks if the law firm is actually just the company's internal IP department."""
    firm = str(row['Law_Firm']).upper()
    comp = str(row['Company']).upper()
    
    # Ignore common first words that might cause false positives
    stopwords = {"THE", "A", "AN", "UNIVERSITY", "BOARD", "TRUSTEES", "REGENTS", "INSTITUTE"}
    
    if comp != 'UNKNOWN' and len(comp.split()) > 0:
        first_word = comp.split()[0].replace(",", "").replace(".", "")
        if len(first_word) > 2 and first_word not in stopwords and first_word in firm:
            return "IN-HOUSE COUNSEL"
            
    return row['Law_Firm']

def generate_landscape_dashboard(csv_path, output_dir):
    df = pd.read_csv(csv_path)
    if df.empty:
        return
        
    keyword = str(df['Keyword'].iloc[0]).title()
    safe_name = os.path.basename(csv_path).replace("_landscape.csv", "")
    
    df['Law_Firm'] = df.apply(clean_in_house_counsel, axis=1)
    sns.set_theme(style="whitegrid", font_scale=1.8)
    
    fig, axes = plt.subplots(2, 2, figsize=(28, 20))
    axes = axes.flatten() 
    
    fig.suptitle(f"Patent Landscape & Target Employers: '{keyword}'", fontsize=40, fontweight='bold', y=0.98)

    # ==========================================
    # PANEL 1: Innovation Velocity (Timeline)
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
        
        yearly_stats.plot(kind='bar', stacked=True, ax=axes[0], color=bar_colors, edgecolor='white', width=0.8)
        
        axes[0].set_title("Innovation Velocity (Filings per Year)", fontsize=28, fontweight='bold')
        axes[0].set_ylabel("Number of Applications", fontsize=24)
        axes[0].set_xlabel("Filing Year", fontsize=24)
        axes[0].tick_params(axis='x', rotation=45, labelsize=20)
        axes[0].tick_params(axis='y', labelsize=20)
        axes[0].legend(title="", fontsize=20, loc='upper left', framealpha=0.9)
    else:
        axes[0].text(0.5, 0.5, "No Date Data Available", ha='center', va='center', fontsize=28)
        axes[0].set_title("Innovation Velocity", fontsize=28, fontweight='bold')

    # ==========================================
    # PANEL 2: Top Companies in this Space
    # ==========================================
    comp_df = df[~df['Company'].fillna('UNKNOWN').str.upper().isin(['UNKNOWN', 'NONE'])]
    
    if not comp_df.empty:
        company_counts = comp_df['Company'].value_counts().head(5)
        
        sns.barplot(y=company_counts.index, x=company_counts.values, ax=axes[1], 
                    hue=company_counts.index, palette="Blues_r", legend=False)
                    
        axes[1].set_title("Top Assignees (Companies)", fontsize=28, fontweight='bold')
        axes[1].set_xlabel("Number of Patents", fontsize=24)
        axes[1].set_ylabel("", fontsize=24)
        
        axes[1].tick_params(axis='x', labelsize=20)
        axes[1].tick_params(axis='y', labelsize=20)
        
        axes[1].set_yticks(axes[1].get_yticks())
        comp_labels = axes[1].get_yticklabels()
        new_labels = [(lbl.get_text()[:25] + '...') if len(lbl.get_text()) > 25 else lbl.get_text() for lbl in comp_labels]
        axes[1].set_yticklabels(new_labels)
    else:
        axes[1].text(0.5, 0.5, "No Assignee Data Found", ha='center', va='center', fontsize=28)
        axes[1].set_title("Top Assignees (Companies)", fontsize=28, fontweight='bold')
        axes[1].axis('off')

    # ==========================================
    # DATA PREP FOR PANELS 3 & 4 (Target Employers)
    # ==========================================
    invalid_firms = ['IN-HOUSE COUNSEL', 'UNKNOWN', 'UNKNOWN / PRO SE', 'NONE']
    ext_df = df[~df['Law_Firm'].fillna('UNKNOWN').str.upper().isin(invalid_firms)]
    top_firms = ext_df['Law_Firm'].value_counts().head(5).index.tolist()
    
    firm_labels = [(f[:30] + '...') if len(f) > 30 else f for f in top_firms]

    if top_firms:
        # ==========================================
        # PANEL 3: Law Firm Portfolio Health (Active Pipeline)
        # ==========================================
        p3_df = ext_df[ext_df['Law_Firm'].isin(top_firms)]
        status_counts = p3_df.groupby(['Law_Firm', 'Lifecycle_Category']).size().unstack(fill_value=0)
        
        # Ensure it maintains the top 5 order
        status_counts = status_counts.reindex(top_firms)
        
        bar_colors = [color_map.get(col, '#7f7f7f') for col in status_counts.columns]
        status_counts.plot(kind='barh', stacked=True, ax=axes[2], color=bar_colors, edgecolor='white', width=0.7)
        
        axes[2].set_title("Target Employers: Active Pipeline & Status", fontsize=28, fontweight='bold')
        axes[2].set_xlabel("Number of Applications Handled", fontsize=24)
        axes[2].set_ylabel("", fontsize=24)
        axes[2].tick_params(axis='both', labelsize=20)
        
        axes[2].set_yticks(range(len(firm_labels)))
        axes[2].set_yticklabels(firm_labels)
        axes[2].invert_yaxis() # Put the highest volume firm at the top
        axes[2].legend(title="", fontsize=18, loc='lower right', framealpha=0.9)

        # ==========================================
        # PANEL 4: Law Firms & Key Corporate Clients
        # ==========================================
        # Custom palette: 1st, 2nd, 3rd Known Clients + Gray for Others/Unknown
        client_colors = ["#4c72b0", "#55a868", "#c44e52", "#d3d3d3"] 
        
        for i, firm in enumerate(top_firms):
            firm_data = ext_df[ext_df['Law_Firm'] == firm]
            total_apps = len(firm_data)
            
            # Find the known clients
            is_known = ~firm_data['Company'].fillna('UNKNOWN').str.upper().isin(['UNKNOWN', 'NONE'])
            known_clients = firm_data[is_known]['Company'].value_counts()
            
            # Get the top 3 known clients
            top_clients = known_clients.head(3)
            
            # Calculate what's left over (Unranked Known + All Unknowns)
            others_unknown_count = total_apps - top_clients.sum()
            
            left = 0
            
            # Draw Top 3 Known Clients
            for j, (client, count) in enumerate(top_clients.items()):
                axes[3].barh(i, count, left=left, color=client_colors[j], edgecolor='white', height=0.7)
                
                # Only draw text if the segment is large enough (> 8% of total width)
                if count >= (total_apps * 0.08):
                    short_client = client[:14] + '..' if len(client) > 14 else client
                    axes[3].text(left + count/2, i, f"{short_client}\n({count})", 
                                 ha='center', va='center', color='white', fontsize=18, fontweight='bold')
                left += count
                
            # Draw 'Others / Unknown'
            if others_unknown_count > 0:
                axes[3].barh(i, others_unknown_count, left=left, color=client_colors[3], edgecolor='white', height=0.7)
                
                if others_unknown_count >= (total_apps * 0.08):
                    axes[3].text(left + others_unknown_count/2, i, f"Others/Unknown\n({others_unknown_count})", 
                                 ha='center', va='center', color='black', fontsize=18, fontweight='bold')

        axes[3].set_title("Target Employers: Key Corporate Clients", fontsize=28, fontweight='bold')
        axes[3].set_xlabel("Applications Segmented by Client", fontsize=24)
        axes[3].set_ylabel("", fontsize=24)
        
        axes[3].set_yticks(range(len(firm_labels)))
        axes[3].set_yticklabels(firm_labels)
        axes[3].tick_params(axis='both', labelsize=20)
        axes[3].invert_yaxis() 
        
    else:
        for ax in [axes[2], axes[3]]:
            ax.text(0.5, 0.5, "No External Law Firm Data Found", ha='center', va='center', fontsize=28)
            ax.axis('off')

    # ==========================================
    # Finish and Save
    # ==========================================
    plt.tight_layout()
    plt.subplots_adjust(top=0.92, wspace=0.35, hspace=0.5) 
    
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