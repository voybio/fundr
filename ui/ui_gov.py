# ui/ui_gov.py

def render_banner_grants(total_opps, unique_agencies, total_program_funding):
    """
    Renders a 3-statistic banner:
      - total_opps (Opportunities)
      - unique_agencies
      - total_program_funding
    """
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
        <div class="value">{total_program_funding}</div>
        <div class="label">Total Program Funding</div>
      </div>
    </div>
    """
    return banner_html


def render_banner_nih(total_docs, unique_orgs, unique_activity):
    """
    Example NIH banner function, if you have separate NIH data.
    Not used for the grants page, but included for completeness.
    """
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
    """
    Renders a card HTML for a single grant row. We display:
      - Title (hyperlinked from AdditionalInformationURL)
      - AgencyName
      - OpportunityID
      - CloseDate
      - ProgramFunding
      - A short snippet (400 chars) of the Description
    """
    title = row.get('OpportunityTitle', 'N/A')
    url = row.get('AdditionalInformationURL', '#')
    title_html = f'<a href="{url}" target="_blank">{title}</a>'

    agency = row.get('AgencyName', 'N/A')
    opp_id = row.get('OpportunityID', 'N/A')
    close_date = row.get('CloseDate', 'N/A')
    program_funding = row.get('EstimatedTotalProgramFunding', 'N/A')

    # Show only a 400-character snippet
    desc_full = row.get('Description', 'N/A') or ""
    desc_snippet = desc_full[:400]
    if len(desc_full) > 400:
        desc_snippet += "..."

    card_html = f"""
    <div class="card" style="margin: 10px;">
      <div class="content">
        <div class="header">{title_html}</div>
        <div class="meta">{agency}</div>
        <div class="description">
          <p><strong>ID:</strong> {opp_id}</p>
          <p><strong>Close Date:</strong> {close_date}</p>
          <p><strong>Program Funding:</strong> {program_funding}</p>
          <p><strong>Description (Snippet):</strong> {desc_snippet}</p>
        </div>
      </div>
    </div>
    """
    return card_html


def render_card_nih(row):
    """
    Example NIH card function. Not used in the grants flow, but here for reference.
    """
    title = row.get('Title', 'N/A')
    url = row.get('URL', '#')
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
    Splits a list of card HTML strings into rows containing up to `cards_per_row` cards each.
    Returns a list of rows, where each row is a list of card HTML strings.
    """
    rows = []
    for i in range(0, len(cards), cards_per_row):
        rows.append(cards[i:i+cards_per_row])
    return rows
