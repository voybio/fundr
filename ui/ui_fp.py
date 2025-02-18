# ui/ui_fp.py


def render_banner_grants(total_opps, unique_agencies, total_budget_str):
    banner_html = f"""
    <div class="ui three small statistics">
      <div class="grey statistic">
        <div class="value">{total_opps}</div>
        <div class="label">Opportunities</div>
      </div>
      <div class="grey statistic">
        <div class="value">{unique_agencies}</div>
        <div class="label">Unique Agencies</div>
      </div>
      <div class="grey statistic">
        <div class="value">{total_budget_str}</div>
        <div class="label">Total Budget</div>
      </div>
    </div>
    """
    return banner_html

def render_banner_nih(total_docs, unique_orgs, unique_activity):
    banner_html = f"""
    <div class="ui three small statistics">
      <div class="grey statistic">
        <div class="value">{total_docs}</div>
        <div class="label">Funding Sources</div>
      </div>
      <div class="grey statistic">
        <div class="value">{unique_orgs}</div>
        <div class="label">Programs</div>
      </div>
      <div class="grey statistic">
        <div class="value">{unique_activity}</div>
        <div class="label">Activity Codes</div>
      </div>
    </div>
    """
    return banner_html

def render_card_grants(row):
    title = row.get('OpportunityTitle', 'N/A')
    opp_id = row.get('OpportunityID', 'N/A')
    agency = row.get('AgencyName', 'N/A')
    post_date = row.get('PostDate', 'N/A')
    budget = row.get('Budget', 'N/A')
    card_html = f"""
    <div class="card" style="margin: 10px;">
        <div class="content">
            <div class="header">{title}</div>
            <div class="meta">{agency}</div>
            <div class="description">
                <p><strong>ID:</strong> {opp_id}</p>
                <p><strong>Post Date:</strong> {post_date}</p>
                <p><strong>Budget:</strong> {budget}</p>
            </div>
        </div>
    </div>
    """
    return card_html

def render_card_nih(row):
    title = row.get('Title', 'N/A')
    url = row.get('URL', '#')
    # Wrap title in hyperlink
    title_html = f'<a href="{url}" target="_blank">{title}</a>'
    release_date = row.get('Release_Date', 'N/A')
    activity = row.get('Activity_Code', 'N/A')
    organization = row.get('Organization', 'N/A')
    doc_type = row.get('Document_Type', 'N/A')
    card_html = f"""
    <div class="card" style="margin: 10px;">
        <div class="content">
            <div class="header">{title_html}</div>
            <div class="meta">{organization}</div>
            <div class="description">
                <p><strong>Release Date:</strong> {release_date}</p>
                <p><strong>Activity:</strong> {activity}</p>
                <p><strong>Document Type:</strong> {doc_type}</p>
            </div>
        </div>
    </div>
    """
    return card_html

def render_cards_grid(cards, cards_per_row=3):
    """
    Split a list of card HTML strings into rows.
    Returns a list of rows; each row is a list of card HTML.
    """
    rows = []
    for i in range(0, len(cards), cards_per_row):
        rows.append(cards[i:i+cards_per_row])
    return rows
