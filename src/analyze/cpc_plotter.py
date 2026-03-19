import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

def plot_cpc_landscape(csv_path, output_dir):
    df = pd.read_csv(csv_path)
    if df.empty: return
        
    tech_name = df['Technology'].iloc[0]
    safe_name = os.path.basename(csv_path).replace("_landscape.csv", "")
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(22, 7))
    fig.suptitle(f"IP Industry Landscape: {tech_name}", fontsize=20, fontweight='bold', y=1.05)

    # PANEL 1: Top 10 Companies (Assignees)
    top_comps = df[df['Company'] != 'UNASSIGNED']['Company'].value_counts().head(10)
    sns.barplot(y=top_comps.index, x=top_comps.values, ax=axes[0], hue=top_comps.index, palette="mako", legend=False)
    axes[0].set_title("Top 10 Patent Filers (Companies)", fontsize=14, fontweight='bold')
    axes[0].set_xlabel("Number of Applications")
    axes[0].set_yticks(axes[0].get_yticks())
    axes[0].set_yticklabels([label.get_text()[:30] + '...' if len(label.get_text()) > 30 else label.get_text() for label in axes[0].get_yticklabels()])

    # PANEL 2: Top 10 Law Firms
    top_firms = df['Law_Firm'].value_counts().head(10)
    sns.barplot(y=top_firms.index, x=top_firms.values, ax=axes[1], hue=top_firms.index, palette="rocket", legend=False)
    axes[1].set_title("Top 10 Law Firms in this Sector", fontsize=14, fontweight='bold')
    axes[1].set_xlabel("Number of Applications")
    axes[1].set_yticks(axes[1].get_yticks())
    axes[1].set_yticklabels([label.get_text()[:30] + '...' if len(label.get_text()) > 30 else label.get_text() for label in axes[1].get_yticklabels()])

    # PANEL 3: Industry Filing Trend
    df['Filing_Date'] = pd.to_datetime(df['Filing_Date'], errors='coerce')
    df['Filing_Year'] = df['Filing_Date'].dt.year

    if not df['Filing_Year'].dropna().empty:
        year_counts = df['Filing_Year'].value_counts().sort_index()
        sns.lineplot(x=year_counts.index, y=year_counts.values, ax=axes[2], marker='o', color='b', linewidth=2.5)
        axes[2].set_title("Industry R&D Velocity (Total Filings)", fontsize=14, fontweight='bold')
        axes[2].set_xlabel("Filing Year")
        axes[2].set_ylabel("Applications")
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{safe_name}_landscape_dashboard.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"📊 Generated Graphic: {output_path}")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    csv_dir = os.path.join(root_dir, "data", "processed")
    output_dir = os.path.join(root_dir, "outputs", "figures")
    os.makedirs(output_dir, exist_ok=True)

    csv_files = glob.glob(os.path.join(csv_dir, "cpc_*_landscape.csv"))
    
    for file in csv_files:
        plot_cpc_landscape(file, output_dir)

if __name__ == "__main__":
    main()