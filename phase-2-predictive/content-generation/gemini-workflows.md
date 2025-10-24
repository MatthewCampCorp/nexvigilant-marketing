# Gemini Content Generation Workflows

## Overview
This document provides practical workflows for using Google's Gemini AI to automate and scale content creation across email, social media, blog posts, and advertising. Each workflow includes prompt templates, quality controls, and integration patterns.

## Content Generation Principles

### Brand Voice Guidelines
Before generating any content, establish clear brand voice parameters:

**NexVigilant Brand Voice**:
- **Tone**: Professional yet approachable, confident but not arrogant
- **Style**: Clear, concise, jargon-free (unless technical audience)
- **Perspective**: Customer-focused, solution-oriented
- **Emotion**: Optimistic, empowering, trustworthy
- **Avoid**: Hyperbole, excessive superlatives, fear-mongering, manipulation

### Quality Control Process
1. **Generation**: AI creates initial draft
2. **Review**: Human reviews for brand alignment, accuracy, compliance
3. **Edit**: Human makes adjustments as needed
4. **Approve**: Final approval by content lead
5. **Publish**: Deploy to channel

**Approval Matrix**:
| Content Type | Auto-Publish | Human Review | Legal Review |
|--------------|--------------|--------------|--------------|
| Email subject lines (A/B test) | ✅ | After 30 days | ❌ |
| Social media posts | ❌ | ✅ | ❌ |
| Blog posts | ❌ | ✅ | ❌ |
| Email body copy | ❌ | ✅ | ❌ |
| Ad copy | ❌ | ✅ | For regulated industries |
| Whitepapers/Ebooks | ❌ | ✅ | ✅ |

## Workflow 1: Email Subject Line Generator

### Use Case
Generate multiple subject line variations for A/B testing to improve email open rates.

### Process

**Step 1: Define Context**
```python
context = {
    "campaign_name": "Q1 Product Launch",
    "product": "Enterprise Analytics Platform",
    "audience_segment": "VP-level decision makers in SaaS companies",
    "campaign_goal": "Drive demo requests",
    "tone": "Professional, value-focused",
    "length": "40-60 characters"
}
```

**Step 2: Construct Prompt**
```python
from vertexai.preview.generative_models import GenerativeModel

model = GenerativeModel("gemini-1.5-pro")

prompt = f"""
You are an expert email marketer. Generate 10 email subject line variations for the following campaign:

Campaign: {context['campaign_name']}
Product: {context['product']}
Audience: {context['audience_segment']}
Goal: {context['campaign_goal']}
Tone: {context['tone']}

Requirements:
- Length: {context['length']}
- Include a clear value proposition
- Create urgency without being pushy
- Avoid spam trigger words (FREE, ACT NOW, URGENT!!!)
- Vary approaches: question, statement, how-to, statistic, personalization

Format output as a numbered list.
"""

response = model.generate_content(prompt)
subject_lines = response.text
```

**Step 3: Example Output**
```
1. How Leading SaaS Companies Are Scaling Analytics in 2025
2. Your Q1 Analytics Strategy: 3 Critical Improvements
3. See Why 500+ VPs Trust Our Analytics Platform
4. Is Your Analytics Stack Ready for Enterprise Scale?
5. Unlock Hidden Revenue: Advanced Analytics for SaaS Leaders
6. 10 Minutes to Better Data Decisions (Exclusive Demo)
7. What's Missing from Your Current Analytics Solution?
8. Join the Analytics Revolution: Live Platform Tour
9. Proven Analytics Framework for High-Growth SaaS
10. Your Competitors Are Already Using This Analytics Advantage
```

**Step 4: A/B Test & Learn**
- Select top 3 subject lines
- A/B test in email campaign
- Track open rates
- Feed results back to future prompts ("Subject line #3 performed best with 32% open rate")

### Integration Pattern

```python
# complete_workflow.py
def generate_subject_lines(campaign_context):
    """Generate and store subject lines in BigQuery for A/B testing"""

    # Generate with Gemini
    subject_lines = call_gemini_api(campaign_context)

    # Parse response
    lines = parse_subject_lines(subject_lines)

    # Store in BigQuery
    from google.cloud import bigquery
    client = bigquery.Client()

    rows_to_insert = [
        {
            "campaign_id": campaign_context['campaign_id'],
            "subject_line": line,
            "generated_at": datetime.now().isoformat(),
            "status": "pending_review"
        }
        for line in lines
    ]

    table_id = "nexvigilant-prod.marketing.generated_subject_lines"
    errors = client.insert_rows_json(table_id, rows_to_insert)

    # Notify team for review
    send_slack_notification(f"10 new subject lines generated for {campaign_context['campaign_name']}")

    return lines
```

## Workflow 2: Social Media Content Calendar

### Use Case
Generate a week's worth of social media posts (LinkedIn, Twitter) aligned with content themes.

### Process

**Step 1: Define Content Themes**
```python
themes = {
    "monday": "Industry Insights / Thought Leadership",
    "tuesday": "Customer Success Story",
    "wednesday": "Product Tip / How-To",
    "thursday": "Data/Research Highlight",
    "friday": "Weekend Inspiration / Culture"
}
```

**Step 2: Batch Prompt**
```python
prompt = f"""
You are a B2B social media strategist for NexVigilant, an enterprise analytics company.

Generate 5 LinkedIn posts (one per day, Monday-Friday) following these content themes:
- Monday: {themes['monday']}
- Tuesday: {themes['tuesday']}
- Wednesday: {themes['wednesday']}
- Thursday: {themes['thursday']}
- Friday: {themes['friday']}

Brand Voice: Professional yet approachable, data-driven, customer-focused
Audience: VP+ decision makers in tech/SaaS companies
Tone: Informative, optimistic, conversational

Requirements for each post:
- 100-150 words
- Include a hook (first sentence grabs attention)
- Provide value (insight, tip, or inspiration)
- End with a call-to-action or question to drive engagement
- Include 3-5 relevant hashtags
- No emojis (professional audience)

Format:
---
[DAY]: [THEME]
[POST TEXT]
[HASHTAGS]
---
"""

response = model.generate_content(prompt)
```

**Step 3: Example Output**
```
---
Monday: Industry Insights
The data analytics market will grow 30% in 2025, but 60% of companies still struggle with basic reporting.

Here's the disconnect: Teams are investing in advanced AI and ML, but their foundational data infrastructure can't support it. It's like building a mansion on a shaky foundation.

The companies winning right now? They're focusing on three things first:
1. Data quality and governance
2. Self-service access for business users
3. Automated insights (not just dashboards)

Only then do they layer in predictive analytics and AI.

What's your organization prioritizing this quarter?

#DataAnalytics #EnterpriseData #BusinessIntelligence #DataStrategy #SaaS
---

Tuesday: Customer Success Story
One year ago, TechCorp's sales team spent 10 hours per week manually pulling reports.

Today? Zero hours.

Here's what changed: They implemented automated, real-time dashboards that deliver insights directly to Slack and email. No more logging into five different systems. No more spreadsheet gymnastics.

The impact:
- 10 hours/week saved per rep
- 25% faster deal cycles
- Data-driven decisions in minutes, not days

The best part? Their data team now focuses on strategic analysis instead of ad-hoc report requests.

Sometimes the biggest wins come from eliminating the smallest frictions.

#CustomerSuccess #SalesEnablement #DataAutomation #Productivity
---

[Additional posts for Wed-Fri...]
```

**Step 4: Approval Workflow**
```python
def social_media_approval_workflow(posts):
    """Send generated posts for approval via Slack"""

    for post in posts:
        # Post to Slack approval channel
        message = f"""
📱 *New Social Post for Approval*

*Day*: {post['day']}
*Theme*: {post['theme']}

*Content*:
{post['text']}

*Hashtags*: {post['hashtags']}

✅ Approve | ✏️ Edit | ❌ Reject
        """

        send_to_slack_with_buttons(channel="social-approvals", message=message)

    # Approved posts automatically scheduled in social media management tool
    # Edited posts go back to Gemini for revision
```

## Workflow 3: Blog Post Outline & Draft Generator

### Use Case
Accelerate blog content creation by generating outlines and first drafts.

### Process

**Step 1: Generate Outline**
```python
prompt = f"""
Generate a detailed blog post outline on the topic: "How to Build a Data-Driven Marketing Strategy in 2025"

Target Audience: Marketing leaders at B2B SaaS companies (100-500 employees)
Post Goal: Establish thought leadership, drive newsletter sign-ups
Length: 1,500-2,000 words
Tone: Educational, actionable, authoritative

Include:
- Attention-grabbing title (SEO-optimized)
- Meta description (155 characters)
- Introduction hook
- 5-7 main sections with subheadings
- Key takeaways for each section
- Conclusion with clear CTA
- Recommended internal links (to pricing page, case studies, related blog posts)

Format the outline with clear headings and bullet points.
"""

response = model.generate_content(prompt)
outline = response.text
```

**Step 2: Review & Refine Outline**
```
Human reviews outline, makes adjustments to structure, adds specific points to include
```

**Step 3: Generate Full Draft**
```python
refined_outline = """
[Human-edited version of outline]
"""

prompt = f"""
Using the following outline, write a complete blog post. Follow the structure exactly, but expand each section with detailed, actionable content.

Outline:
{refined_outline}

Requirements:
- Write in a professional yet conversational tone
- Include specific examples and actionable tips
- Add transition sentences between sections
- Use short paragraphs (2-3 sentences max) for readability
- Include pull quotes (marked with ">") for key insights
- Suggest image/graphic placement with [IMAGE: description]
- Cite statistics where appropriate (can be generic, human will verify)

Write the full blog post now:
"""

response = model.generate_content(prompt)
blog_draft = response.text
```

**Step 4: Human Editing**
- Content marketer reviews and edits for accuracy, brand voice, SEO
- Fact-checks any statistics or claims
- Adds real examples and customer stories
- Optimizes for target keywords
- Creates custom images/graphics

**Step 5: SEO Optimization**
```python
# Use Gemini to suggest SEO improvements
seo_prompt = f"""
Review this blog post and suggest SEO optimizations:

{blog_draft}

Target Keyword: "data-driven marketing strategy"
Secondary Keywords: "marketing analytics", "customer data platform", "marketing attribution"

Provide:
1. Keyword density analysis (is primary keyword used enough?)
2. Suggestions for internal links
3. Meta title and description
4. Header tag recommendations (H1, H2, H3 structure)
5. Image alt text suggestions
"""

seo_suggestions = model.generate_content(seo_prompt)
```

## Workflow 4: Personalized Email Copy Generator

### Use Case
Create personalized email body copy for different customer segments.

### Process

**Step 1: Define Segments & Personalization Variables**
```python
segments = {
    "high_clv_customers": {
        "profile": "Customers with CLV > $50k, been with us 2+ years",
        "pain_point": "Scaling challenges, need advanced features",
        "offer": "Exclusive early access to Enterprise tier",
        "tone": "VIP, appreciative, forward-looking"
    },
    "churn_risk_customers": {
        "profile": "Customers with churn risk > 70%, declining usage",
        "pain_point": "Not seeing value, may have implementation issues",
        "offer": "Free 30-minute consultation with success manager",
        "tone": "Supportive, helpful, customer-focused"
    },
    "trial_users_high_engagement": {
        "profile": "Day 10 of 14-day trial, high usage, visited pricing 3x",
        "pain_point": "Evaluating options, needs final push to convert",
        "offer": "20% discount if they convert before trial ends",
        "tone": "Encouraging, value-focused, time-sensitive"
    }
}
```

**Step 2: Generate Segment-Specific Email**
```python
def generate_personalized_email(segment_name, segment_data):
    prompt = f"""
Write a personalized email for the following customer segment:

Segment: {segment_name}
Profile: {segment_data['profile']}
Pain Point: {segment_data['pain_point']}
Offer: {segment_data['offer']}
Desired Tone: {segment_data['tone']}

Email Requirements:
- Subject line (40-60 characters)
- Personalized greeting (use {{{{first_name}}}})
- Acknowledge their specific situation/behavior
- Empathize with pain point
- Present offer as a solution
- Clear, single call-to-action button
- 150-200 words
- Professional but warm sign-off

Generate the email:
"""

    response = model.generate_content(prompt)
    return response.text
```

**Step 3: Example Output for "churn_risk_customers"**
```
Subject: We're Here to Help, {{first_name}}

Hi {{first_name}},

I noticed your team's activity has slowed down over the past few weeks, and I wanted to check in.

At NexVigilant, our goal is to make sure you're getting maximum value from your analytics platform. If you're facing any challenges—whether it's data integration, training your team, or just finding the right workflow—we're here to help.

I'd like to offer you a complimentary 30-minute consultation with Sarah, one of our senior customer success managers. She's helped hundreds of teams optimize their setup and can provide tailored recommendations for your specific use case.

No pressure, no sales pitch—just genuine support to help you succeed.

[Schedule Your Free Consultation]

Looking forward to helping you get the most out of NexVigilant.

Best,
Mike Chen
Customer Success Team
NexVigilant
```

**Step 4: Dynamic Insertion & Testing**
```python
# Integrate with Braze
def send_personalized_emails(segment_name):
    # Get generated email template
    email_content = generate_personalized_email(segment_name, segments[segment_name])

    # Parse subject and body
    subject, body = parse_email(email_content)

    # Create Braze campaign
    braze_campaign = {
        "name": f"Personalized - {segment_name}",
        "subject": subject,
        "body": body,  # Will use Liquid syntax for {{first_name}}
        "segment": segment_name,
        "send_time": "optimal"  # Braze Intelligent Timing
    }

    # Send via Braze API
    send_via_braze(braze_campaign)
```

## Workflow 5: Ad Copy Variations at Scale

### Use Case
Generate hundreds of ad copy variations for programmatic A/B testing.

### Process

**Step 1: Define Ad Creative Matrix**
```python
creative_matrix = {
    "value_props": [
        "Reduce reporting time by 80%",
        "Make data-driven decisions in minutes",
        "Unify all your marketing data in one place"
    ],
    "pain_points": [
        "Tired of manual reports?",
        "Drowning in spreadsheets?",
        "Can't get the insights you need fast enough?"
    ],
    "ctas": [
        "Start Your Free Trial",
        "Get a Demo",
        "See It In Action"
    ],
    "formats": ["headline", "description", "headline + description"]
}
```

**Step 2: Batch Generate All Combinations**
```python
def generate_ad_variations(value_prop, pain_point, cta, format):
    prompt = f"""
Generate Google Search ad copy (Responsive Search Ad format).

Value Proposition: {value_prop}
Pain Point: {pain_point}
Call-to-Action: {cta}
Format: {format}

Requirements:
- Headlines: Max 30 characters each
- Descriptions: Max 90 characters each
- Include target keyword: "marketing analytics platform"
- Professional, benefit-focused tone
- Avoid superlatives and hype

Generate:
- 5 headline variations
- 3 description variations
"""

    response = model.generate_content(prompt)
    return response.text

# Generate all combinations
import itertools
all_ads = []

for vp, pp, cta in itertools.product(
    creative_matrix['value_props'],
    creative_matrix['pain_points'],
    creative_matrix['ctas']
):
    ad_copy = generate_ad_variations(vp, pp, cta, "headline + description")
    all_ads.append({
        "value_prop": vp,
        "pain_point": pp,
        "cta": cta,
        "copy": ad_copy
    })

print(f"Generated {len(all_ads)} ad variations")  # 27 variations
```

**Step 3: Upload to Google Ads**
```python
from google.ads.googleads.client import GoogleAdsClient

def upload_ad_variations(ads):
    """Upload generated ads to Google Ads as Responsive Search Ads"""

    client = GoogleAdsClient.load_from_storage()

    for ad in ads:
        # Parse headlines and descriptions
        headlines = parse_headlines(ad['copy'])
        descriptions = parse_descriptions(ad['copy'])

        # Create Responsive Search Ad
        rsa_operation = create_rsa(
            headlines=headlines,
            descriptions=descriptions,
            final_url="https://nexvigilant.com/demo"
        )

        # Upload to Google Ads
        client.mutate(rsa_operation)

    print(f"Uploaded {len(ads)} ads to Google Ads")
```

## Workflow 6: Product Description Generator (E-commerce)

### Use Case
For companies with large product catalogs, generate SEO-optimized product descriptions at scale.

### Process

```python
def generate_product_description(product_data):
    prompt = f"""
Write an SEO-optimized product description for:

Product Name: {product_data['name']}
Category: {product_data['category']}
Key Features: {product_data['features']}
Target Audience: {product_data['audience']}
Price Point: {product_data['price_point']}

Requirements:
- 150-200 words
- Include target keywords naturally: {product_data['seo_keywords']}
- Highlight 3 main benefits (not just features)
- Address a customer pain point
- Include a soft call-to-action
- Professional yet engaging tone

Generate the product description:
"""

    response = model.generate_content(prompt)
    return response.text

# Batch process entire catalog
products = load_products_from_bigquery()

for product in products:
    description = generate_product_description(product)

    # Store in database
    update_product_description(product['id'], description)

    # Trigger human review queue for high-value products (>$1000)
    if product['price'] > 1000:
        send_for_review(product['id'], description)
```

## Advanced: Multi-Modal Content Generation

### Generate Social Media Images with Imagen

```python
from vertexai.preview.vision_models import ImageGenerationModel

def generate_social_image(post_content):
    """Generate a custom image for a social media post"""

    # Extract key theme from post
    theme_prompt = f"""
    Summarize this social media post in one visual concept (10 words max):
    {post_content}
    """
    theme = model.generate_content(theme_prompt).text

    # Generate image with Imagen
    imagen = ImageGenerationModel.from_pretrained("imagegeneration@005")

    image_prompt = f"""
    Professional, modern business illustration:
    {theme}

    Style: Minimalist, clean, corporate
    Colors: Blues and grays (professional)
    No text, no people
    Suitable for LinkedIn post
    """

    images = imagen.generate_images(
        prompt=image_prompt,
        number_of_images=1,
        aspect_ratio="1:1"
    )

    # Save image
    images[0].save(f"social_image_{post_id}.png")

    return f"social_image_{post_id}.png"
```

## Quality Control & Brand Safety

### Automated Content Checks

```python
def quality_check(generated_content):
    """Run automated quality checks on generated content"""

    checks = {
        "brand_voice": check_brand_voice(generated_content),
        "tone": check_tone(generated_content),
        "spam_words": check_spam_trigger_words(generated_content),
        "length": check_length_requirements(generated_content),
        "spelling": run_spell_check(generated_content),
        "readability": calculate_readability_score(generated_content),
        "seo": check_keyword_usage(generated_content)
    }

    # Flag for human review if any check fails
    if not all(checks.values()):
        flag_for_review(generated_content, failed_checks=checks)

    return checks

def check_spam_trigger_words(content):
    """Check for spam trigger words that could hurt deliverability"""
    spam_words = ["FREE", "ACT NOW", "LIMITED TIME", "CLICK HERE", "GUARANTEE", "NO RISK"]

    content_upper = content.upper()
    found_spam = [word for word in spam_words if word in content_upper]

    if found_spam:
        print(f"⚠️ Spam trigger words found: {found_spam}")
        return False

    return True
```

### Human-in-the-Loop Review Dashboard

```python
# Streamlit app for content review
import streamlit as st

st.title("AI-Generated Content Review Dashboard")

# Load pending content
pending_content = load_from_bigquery("SELECT * FROM marketing.generated_content WHERE status = 'pending_review'")

for item in pending_content:
    st.subheader(f"{item['content_type']} - {item['campaign_name']}")

    st.write("**Generated Content:**")
    st.text_area("", value=item['content'], height=200, key=f"content_{item['id']}")

    st.write("**Quality Checks:**")
    st.json(item['quality_checks'])

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve", key=f"approve_{item['id']}"):
            approve_content(item['id'])
            st.success("Approved!")

    with col2:
        if st.button("✏️ Edit", key=f"edit_{item['id']}"):
            # Open in editor
            st.session_state['editing'] = item['id']

    with col3:
        if st.button("❌ Reject", key=f"reject_{item['id']}"):
            reject_content(item['id'])
            st.error("Rejected")

    st.markdown("---")
```

## Performance Tracking

### Track AI-Generated vs. Human-Written Performance

```sql
-- Compare performance of AI-generated vs human-written content
SELECT
  content_source,  -- 'ai_generated' or 'human_written'
  content_type,    -- 'email', 'social', 'blog', 'ad'
  COUNT(*) AS total_pieces,
  AVG(open_rate) AS avg_open_rate,
  AVG(click_rate) AS avg_click_rate,
  AVG(conversion_rate) AS avg_conversion_rate,
  AVG(engagement_score) AS avg_engagement
FROM marts.content_performance
WHERE created_date >= CURRENT_DATE() - 90
GROUP BY content_source, content_type
ORDER BY content_type, avg_conversion_rate DESC
```

### Continuous Improvement Loop

1. **Analyze Performance**: Which AI-generated content performs best?
2. **Extract Patterns**: What do high-performing pieces have in common?
3. **Update Prompts**: Refine prompts based on learnings
4. **A/B Test**: Continuously test new prompt variations
5. **Iterate**: Repeat monthly

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Owner**: Content Marketing & AI Team
**Next Review**: Monthly performance review
