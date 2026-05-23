"""
nlu_training_data_full.py

This module defines a comprehensive multi-label training dataset for our NLU pipeline.
There are at least 30 examples for each finalized intent.
"""

# Finalized intents:
INTENTS = [
    # A. Crunchbase Data–Based Intents
    "COMPANY_PROFILE_QUERY",
    "FUNDING_ROUND_QUERY",
    "ACQUISITION_QUERY",
    "IPO_QUERY",
    "INVESTOR_QUERY",
    "INVESTMENT_DETAILS_QUERY",
    "ORGANIZATION_RELATIONSHIP_QUERY",
    "INVESTMENT_PARTNER_QUERY",
    "FUNDS_QUERY",
    "JOBS_QUERY",
    "PEOPLE_PROFILE_QUERY",
    "EDUCATION_QUERY",
    "COMPETITOR_LOOKUP",
    "LEAD_GENERATION_QUERY",
    "MARKET_ANALYSIS_QUERY",
    # B. News, TechCrunch, and Startup News–Based Intents
    "TECH_NEWS_QUERY",
    "FUNDING_NEWS_QUERY",
    "EVENT_QUERY",
    "MARKET_TRENDS_QUERY",
]

def multi_cat_dict(active_intents):
    """
    Returns a dictionary for the text categorizer where each intent in active_intents is given a score of 1.0,
    and all other intents are given a score of 0.0.
    """
    return {intent: 1.0 if intent in active_intents else 0.0 for intent in INTENTS}

# -----------------------------------------------------------------------------
# A. Crunchbase Data–Based Intents
# -----------------------------------------------------------------------------

# 1. COMPANY_PROFILE_QUERY (30 examples)
company_profile_examples = [
    "Show me Apple's company profile.",
    "Get me the detailed company profile for Google.",
    "I need the company profile for Microsoft.",
    "What is the profile of Amazon?",
    "Give me an overview of Tesla.",
    "Display Facebook's company profile.",
    "Provide me with the company profile for Netflix.",
    "Can you show me the profile of Uber?",
    "Fetch the company profile details for Airbnb.",
    "I want to see LinkedIn's company profile.",
    "Show me a detailed profile of Adobe.",
    "Retrieve the company profile for Intel.",
    "What is the company profile of IBM?",
    "Give me the company profile of Oracle.",
    "Find the company profile for Cisco.",
    "Provide the profile details for Salesforce.",
    "Display the company profile for SAP.",
    "I need a detailed profile of Qualcomm.",
    "Show me the corporate profile of HP.",
    "Fetch the company profile for Dell.",
    "I want to view the company profile of eBay.",
    "Get me the company profile for Twitter.",
    "Show me the profile of Snapchat.",
    "Retrieve the company profile for Pinterest.",
    "I need the detailed company profile for Square.",
    "Show me the company profile for Shopify.",
    "Can you provide the company profile for Slack?",
    "Display the company profile of Zoom.",
    "Give me the detailed profile for Atlassian.",
    "Fetch the company profile details for Dropbox.",
]

# 2. FUNDING_ROUND_QUERY (30 examples)
funding_round_examples = [
    "What funding rounds has Apple completed?",
    "Show me the latest funding round for Google.",
    "Get details on Microsoft's funding rounds.",
    "List Amazon's funding round history.",
    "Tell me about Tesla's latest funding round.",
    "Give me details of Facebook's recent funding round.",
    "I want information on Netflix's funding rounds.",
    "Show the funding rounds for Uber.",
    "Fetch details on Airbnb's funding rounds.",
    "Provide the funding history for LinkedIn.",
    "What are the funding rounds for Adobe?",
    "Retrieve information on Intel's funding rounds.",
    "Show me the funding round details for IBM.",
    "Get details on Oracle's funding rounds.",
    "List the funding rounds for Cisco.",
    "Provide information on Salesforce's funding rounds.",
    "Tell me about SAP's funding history.",
    "What funding rounds did Qualcomm go through?",
    "Show the funding rounds for HP.",
    "Give me details on Dell's funding rounds.",
    "Fetch the funding round data for eBay.",
    "I want to see Twitter's funding rounds.",
    "Display funding rounds for Snapchat.",
    "Show me the funding history of Pinterest.",
    "Get details on Square's funding rounds.",
    "Provide the funding round details for Shopify.",
    "Tell me about Slack's funding rounds.",
    "List the funding rounds for Zoom.",
    "Fetch details on Atlassian's funding rounds.",
    "Retrieve information on Dropbox's funding rounds.",
]

# 3. ACQUISITION_QUERY (30 examples)
acquisition_examples = [
    "What acquisitions has Apple made?",
    "Show me Apple's acquisition history.",
    "List the companies acquired by Google.",
    "Tell me about Microsoft's acquisitions.",
    "What acquisitions did Amazon complete?",
    "Give me details on Tesla's acquisitions.",
    "Display Facebook's acquisition activity.",
    "I want to see Netflix's acquisition history.",
    "Provide details on Uber's acquisitions.",
    "Show me the companies acquired by Airbnb.",
    "List LinkedIn's acquisition history.",
    "What acquisitions has Adobe done?",
    "Fetch Intel's acquisition details.",
    "Get information on IBM's acquisitions.",
    "Show Oracle's acquisition history.",
    "Tell me about Cisco's acquisitions.",
    "What acquisitions has Salesforce made?",
    "Display SAP's acquisition record.",
    "List Qualcomm's acquisitions.",
    "Provide details on HP's acquisitions.",
    "Show Dell's acquisition history.",
    "Fetch information on eBay's acquisitions.",
    "What acquisitions has Twitter completed?",
    "Show Snapchat's acquisition details.",
    "List Pinterest's acquisition history.",
    "Tell me about Square's acquisitions.",
    "Provide details on Shopify's acquisitions.",
    "What acquisitions has Slack made?",
    "Display Zoom's acquisition activity.",
    "List Atlassian's acquisitions.",
]

# 4. IPO_QUERY (30 examples)
ipo_examples = [
    "Which companies have gone public recently?",
    "Show me the IPO details for Apple.",
    "What are the IPO dates for Google?",
    "Tell me about Microsoft's IPO.",
    "Provide IPO information for Amazon.",
    "Display Tesla's IPO details.",
    "Fetch the IPO profile for Facebook.",
    "Show me Netflix's IPO data.",
    "What is Uber's IPO information?",
    "Give me the IPO details of Airbnb.",
    "Show me LinkedIn's IPO history.",
    "Provide Adobe's IPO details.",
    "Retrieve Intel's IPO information.",
    "What are IBM's IPO details?",
    "Show me Oracle's IPO profile.",
    "Tell me about Cisco's IPO.",
    "Get the IPO details for Salesforce.",
    "Display SAP's IPO information.",
    "What is Qualcomm's IPO data?",
    "Fetch HP's IPO details.",
    "Show me Dell's IPO history.",
    "Provide eBay's IPO details.",
    "What are Twitter's IPO details?",
    "Display Snapchat's IPO information.",
    "Tell me about Pinterest's IPO.",
    "Give me the IPO details for Square.",
    "Show Shopify's IPO information.",
    "Retrieve Slack's IPO details.",
    "What are Zoom's IPO details?",
    "Provide Atlassian's IPO information.",
]

# 5. INVESTOR_QUERY (30 examples)
investor_query_examples = [
    "Show me profiles of top investors in the startup ecosystem.",
    "Who are the leading investors in tech startups?",
    "Retrieve details about venture capital firms investing in AI.",
    "List the top investors for biotech startups.",
    "Give me profiles of investors in renewable energy.",
    "Provide information on investors in fintech.",
    "What investors are active in the gaming sector?",
    "Show me profiles of angel investors in Silicon Valley.",
    "List prominent investors in mobile technology.",
    "Retrieve details on investors focusing on enterprise software.",
    "Who are the investors behind successful unicorns?",
    "Give me the profiles of investors in e-commerce.",
    "Show me the network of investors investing in cloud computing.",
    "List top global investors in health tech.",
    "Retrieve profiles of investors in edtech.",
    "Provide details on investors active in the cleantech sector.",
    "Who are the key investors in automotive technology?",
    "Show me profiles of investors in VR and AR.",
    "List investors in cybersecurity.",
    "Retrieve details on investors backing consumer tech startups.",
    "Provide investor profiles for blockchain startups.",
    "Who are the investors investing in SaaS companies?",
    "Give me profiles of investors in social media startups.",
    "Show me details on investors in digital media.",
    "List the leading investors in IoT startups.",
    "Retrieve profiles of investors in robotics.",
    "Provide information on investors in health and wellness tech.",
    "Who are the top investors in the logistics sector?",
    "Show me profiles of investors in real estate tech.",
    "List prominent investors in AR/VR startups.",
]

# 6. INVESTMENT_DETAILS_QUERY (30 examples)
investment_details_examples = [
    "Give me the investment history for Apple.",
    "Show me the past investments made by Google.",
    "Retrieve the investment details for Microsoft.",
    "What investments has Amazon received?",
    "Provide the investment history for Tesla.",
    "Display Facebook's past investment details.",
    "Show me the investment timeline for Netflix.",
    "Give me the investment details for Uber.",
    "What investments has Airbnb secured?",
    "Retrieve the investment history for LinkedIn.",
    "Show me Adobe's investment details.",
    "Provide the investment history for Intel.",
    "What are IBM's past investments?",
    "Retrieve Oracle's investment details.",
    "Show me Cisco's investment history.",
    "Give me the investment details for Salesforce.",
    "Provide SAP's investment timeline.",
    "Display Qualcomm's investment history.",
    "What investments has HP received?",
    "Show me Dell's investment details.",
    "Retrieve eBay's investment history.",
    "Give me the investment timeline for Twitter.",
    "Show me Snapchat's investment details.",
    "Provide Pinterest's investment history.",
    "What investments has Square received?",
    "Retrieve Shopify's investment details.",
    "Show me Slack's investment timeline.",
    "Give me the investment history for Zoom.",
    "What are Atlassian's investment details?",
    "Provide Dropbox's investment timeline.",
]

# 7. ORGANIZATION_RELATIONSHIP_QUERY (30 examples)
org_relationship_examples = [
    "Show me the parent company of YouTube.",
    "What is the subsidiary relationship of Alphabet?",
    "Retrieve details on the organizational hierarchy of Samsung.",
    "Give me the parent-subsidiary structure of Microsoft.",
    "Display the relationship between Facebook and its subsidiaries.",
    "List the parent companies for companies in the tech sector.",
    "What are the subsidiaries of Alphabet?",
    "Show me the corporate relationships within the Apple group.",
    "Provide details on the organizational structure of Google.",
    "Retrieve the parent company of Instagram.",
    "Give me the parent-subsidiary relationships for Amazon.",
    "What is the corporate hierarchy for Oracle?",
    "Show me the organizational relationships for Cisco.",
    "List the subsidiaries of IBM.",
    "Provide details on Hewlett-Packard's organizational structure.",
    "Retrieve the parent company of LinkedIn.",
    "What is the subsidiary structure of Sony?",
    "Display the corporate relationships within the Samsung group.",
    "Show me the parent organization of WhatsApp.",
    "Give me details on the organizational hierarchy for Dell.",
    "List the subsidiaries under Intel.",
    "What is the parent-subsidiary relationship for Adobe?",
    "Show me the organizational structure for Salesforce.",
    "Retrieve details on the relationship between Microsoft and LinkedIn.",
    "Provide the parent company details for YouTube.",
    "What are the organizational relationships for Twitter?",
    "Display the parent-subsidiary structure for Panasonic.",
    "Give me the relationship details of IBM's corporate structure.",
    "List the subsidiaries of Oracle.",
    "Show me the parent company of Slack.",
]

# 8. INVESTMENT_PARTNER_QUERY (30 examples)
investment_partner_examples = [
    "Who are the co-investors in Apple's latest funding round?",
    "List the investment partners for Google in its recent round.",
    "Show me the co-investors for Microsoft's latest funding round.",
    "Retrieve the investment partners involved in Amazon's funding.",
    "Give me the co-investors for Tesla's recent round.",
    "Display the investment partners for Facebook.",
    "Who co-invested in Netflix's last funding round?",
    "Show me the co-investors for Uber.",
    "List the investment partners for Airbnb's funding round.",
    "Provide details on LinkedIn's co-investors.",
    "Who are the co-investors in Adobe's latest round?",
    "Retrieve the investment partners for Intel.",
    "Show me the co-investors for IBM's funding round.",
    "List the co-investment partners for Oracle.",
    "Give me details on Cisco's investment partners.",
    "Display the co-investors for Salesforce's funding round.",
    "Who are the co-investors in SAP's latest round?",
    "Show me the investment partners for Qualcomm.",
    "List the co-investors for HP's funding round.",
    "Retrieve details on Dell's investment partners.",
    "Who co-invested in eBay's latest funding round?",
    "Show me the co-investors for Twitter.",
    "List the investment partners for Snapchat's round.",
    "Provide details on Pinterest's co-investors.",
    "Who are the co-investors in Square's latest funding round?",
    "Retrieve the investment partners for Shopify.",
    "Show me the co-investors for Slack.",
    "List the investment partners for Zoom's funding round.",
    "Give me details on Atlassian's co-investors.",
    "Display the co-investors for Dropbox's funding round.",
]

# 9. FUNDS_QUERY (30 examples)
funds_query_examples = [
    "Show me details on Sequoia Capital's funds.",
    "Retrieve information on Andreessen Horowitz's funds.",
    "Give me the fund details for SoftBank.",
    "What are the details of Accel's investment funds?",
    "Display the funds managed by Greylock Partners.",
    "Provide information on Kleiner Perkins' funds.",
    "Show me details on Bessemer Venture Partners' funds.",
    "Retrieve the fund information for Lightspeed Venture Partners.",
    "Give me details on Founders Fund's investment funds.",
    "What are the details of Benchmark's funds?",
    "Display the funds managed by Tiger Global.",
    "Provide information on New Enterprise Associates' funds.",
    "Show me details on Index Ventures' funds.",
    "Retrieve information on Union Square Ventures' funds.",
    "Give me the fund details for Insight Venture Partners.",
    "What are the details of General Catalyst's funds?",
    "Display the funds managed by DFJ.",
    "Provide information on Battery Ventures' funds.",
    "Show me details on Redpoint Ventures' funds.",
    "Retrieve the fund information for Menlo Ventures.",
    "Give me details on RRE Ventures' funds.",
    "What are the details of CRV's funds?",
    "Display the funds managed by Shasta Ventures.",
    "Provide information on First Round Capital's funds.",
    "Show me details on Social Capital's investment funds.",
    "Retrieve information on Venrock's funds.",
    "Give me the fund details for Upfront Ventures.",
    "What are the details of Sapphire Ventures' funds?",
    "Display the funds managed by Revolution Ventures.",
    "Provide information on Intel Capital's funds.",
]

# 10. JOBS_QUERY (30 examples)
jobs_query_examples = [
    "Show me current job openings at Apple.",
    "List the latest job openings for Google.",
    "Retrieve recent job postings at Microsoft.",
    "What are the current job listings for Amazon?",
    "Display job openings at Tesla.",
    "Provide job listings for Facebook.",
    "Show me recent job postings at Netflix.",
    "Retrieve current job openings at Uber.",
    "List job postings for Airbnb.",
    "What are the latest job openings at LinkedIn?",
    "Display job listings for Adobe.",
    "Show me current job postings at Intel.",
    "Retrieve job openings for IBM.",
    "List job postings at Oracle.",
    "What are the current job openings at Cisco?",
    "Display job listings for Salesforce.",
    "Provide job postings for SAP.",
    "Show me recent job openings at Qualcomm.",
    "Retrieve job listings for HP.",
    "List current job openings at Dell.",
    "What are the latest job postings for eBay?",
    "Display job listings for Twitter.",
    "Show me job openings at Snapchat.",
    "Retrieve job postings for Pinterest.",
    "List current job openings at Square.",
    "What are the job postings for Shopify?",
    "Display job listings for Slack.",
    "Show me recent job openings at Zoom.",
    "Retrieve job postings for Atlassian.",
    "List job openings at Dropbox.",
]

# 11. PEOPLE_PROFILE_QUERY (30 examples)
people_profile_examples = [
    "Show me the profile of Elon Musk.",
    "Retrieve the profile of Jeff Bezos.",
    "Give me the profile of Sundar Pichai.",
    "What is the profile of Mark Zuckerberg?",
    "Display the profile of Tim Cook.",
    "Show me the profile of Satya Nadella.",
    "Retrieve the profile of Larry Page.",
    "Give me the profile of Sergey Brin.",
    "What is the profile of Jack Dorsey?",
    "Display the profile of Marissa Mayer.",
    "Show me the profile of Sheryl Sandberg.",
    "Retrieve the profile of Reed Hastings.",
    "Give me the profile of Brian Chesky.",
    "What is the profile of Drew Houston?",
    "Display the profile of Steve Jobs.",
    "Show me the profile of Bill Gates.",
    "Retrieve the profile of Jeff Weiner.",
    "Give me the profile of Meg Whitman.",
    "What is the profile of Michael Dell?",
    "Display the profile of Larry Ellison.",
    "Show me the profile of Paul Allen.",
    "Retrieve the profile of Steve Ballmer.",
    "Give me the profile of Ginni Rometty.",
    "What is the profile of Indra Nooyi?",
    "Display the profile of Ursula Burns.",
    "Show me the profile of Marc Benioff.",
    "Retrieve the profile of Travis Kalanick.",
    "Give me the profile of Anne Wojcicki.",
    "What is the profile of Eric Schmidt?",
    "Display the profile of Peter Thiel.",
]

# 12. EDUCATION_QUERY (30 examples)
education_examples = [
    "What is Elon Musk's educational background?",
    "Show me the degrees held by Jeff Bezos.",
    "Retrieve the educational qualifications of Sundar Pichai.",
    "What is Mark Zuckerberg's educational history?",
    "Display Tim Cook's academic background.",
    "Show me Satya Nadella's education details.",
    "Retrieve the educational background of Larry Page.",
    "What degrees do Sergey Brin hold?",
    "Provide details on Jack Dorsey's education.",
    "What is Marissa Mayer's academic history?",
    "Show me Sheryl Sandberg's educational background.",
    "Retrieve the degrees earned by Reed Hastings.",
    "What is Brian Chesky's educational qualification?",
    "Display Drew Houston's academic credentials.",
    "Show me Steve Jobs' education history.",
    "What is Bill Gates' educational background?",
    "Retrieve Jeff Weiner's academic details.",
    "Provide the educational background of Meg Whitman.",
    "What degrees does Michael Dell have?",
    "Show me Larry Ellison's academic credentials.",
    "Retrieve Paul Allen's education history.",
    "What is Steve Ballmer's educational background?",
    "Display Ginni Rometty's academic details.",
    "What is Indra Nooyi's educational background?",
    "Show me Ursula Burns' academic credentials.",
    "Retrieve Marc Benioff's education history.",
    "What is Travis Kalanick's educational background?",
    "Display Anne Wojcicki's academic details.",
    "What degrees does Eric Schmidt hold?",
    "Show me Peter Thiel's educational background.",
]

# 13. COMPETITOR_LOOKUP (30 examples)
competitor_lookup_examples = [
    "Who are the main competitors of Apple?",
    "List Google's top competitors.",
    "Show me the competitors of Microsoft.",
    "Identify Amazon's key competitors.",
    "Who competes with Tesla in the market?",
    "List Facebook's competitors.",
    "What are the main competitors of Netflix?",
    "Identify Uber's competitors.",
    "Show me the competitors of Airbnb.",
    "List LinkedIn's competitor companies.",
    "Who are Adobe's main competitors?",
    "Identify Intel's competitors.",
    "Show me the competitors of IBM.",
    "List Oracle's key competitors.",
    "What are Cisco's competitor companies?",
    "Identify Salesforce's main competitors.",
    "Who competes with SAP in the industry?",
    "List Qualcomm's competitors.",
    "Show me the competitors of HP.",
    "Identify Dell's key competitors.",
    "Who are the competitors of eBay?",
    "List Twitter's competitor companies.",
    "What are Snapchat's competitors?",
    "Identify Pinterest's main competitors.",
    "Show me the competitors of Square.",
    "List Shopify's key competitors.",
    "Who competes with Slack in the market?",
    "Identify Zoom's competitors.",
    "Show me the competitors of Atlassian.",
    "List Dropbox's main competitors.",
]

# 14. LEAD_GENERATION_QUERY (30 examples)
lead_generation_examples = [
    "Identify companies in cybersecurity that recently secured funding.",
    "Show me startups in AI that are potential sales leads.",
    "List emerging fintech companies for lead generation.",
    "Find companies in health tech with recent funding rounds.",
    "Identify promising e-commerce startups as leads.",
    "Show me potential sales leads in the SaaS sector.",
    "List cybersecurity firms with recent funding for lead generation.",
    "Find startups in renewable energy that could be sales prospects.",
    "Identify companies in the edtech space for lead generation.",
    "Show me potential leads among digital media startups.",
    "List companies in the blockchain sector that received funding.",
    "Find startups in the IoT space for sales outreach.",
    "Identify promising consumer tech companies as leads.",
    "Show me sales leads in the mobile app industry.",
    "List emerging biotech startups for lead generation.",
    "Find innovative AR/VR startups as potential sales leads.",
    "Identify promising robotics companies for outreach.",
    "Show me potential leads in the gaming industry.",
    "List companies in the SaaS space with recent investments.",
    "Find digital health startups that are good sales prospects.",
    "Identify promising cleantech companies for lead generation.",
    "Show me companies in the logistics tech sector for lead generation.",
    "List startups in the travel tech space as potential leads.",
    "Find companies in the food tech sector for lead generation.",
    "Identify emerging adtech startups as sales leads.",
    "Show me companies in the influencer marketing space for outreach.",
    "List fashion tech startups with recent funding rounds.",
    "Find companies in the automotive tech space as potential leads.",
    "Identify promising startups in the sports tech sector for lead generation.",
    "Show me potential sales leads in the digital payments space.",
]

# 15. MARKET_ANALYSIS_QUERY (30 examples)
market_analysis_examples = [
    "Provide an analysis of the top 5 players in the cloud computing market.",
    "Show me a market analysis of the fintech sector.",
    "What are the current trends in the startup ecosystem?",
    "Give me a market overview of the health tech industry.",
    "Provide insights into the competitive landscape of the AI sector.",
    "Show me a market analysis of the e-commerce industry.",
    "What are the key market trends in digital media?",
    "Give me an analysis of the SaaS market.",
    "Provide a market overview of the cybersecurity sector.",
    "Show me current trends in renewable energy startups.",
    "What is the market analysis for the blockchain industry?",
    "Give me insights into the cloud services market.",
    "Provide a competitive analysis of the online retail market.",
    "Show me a market overview of the IoT sector.",
    "What are the key trends in the mobile app industry?",
    "Give me an analysis of the edtech market.",
    "Provide market insights into the VR/AR industry.",
    "Show me the current state of the gaming market.",
    "What is the market analysis for the digital health sector?",
    "Give me a market overview of the startup ecosystem.",
    "Provide insights into the logistics tech market.",
    "Show me a market analysis of the enterprise software sector.",
    "What are the trends in the social media market?",
    "Give me an analysis of the automotive tech industry.",
    "Provide a market overview of the travel tech sector.",
    "Show me the competitive landscape of the adtech industry.",
    "What is the market analysis for the influencer marketing sector?",
    "Give me insights into the fashion tech market.",
    "Provide a market overview of the digital payments space.",
    "Show me current trends in the sports tech market.",
]

# -----------------------------------------------------------------------------
# B. News, TechCrunch, and Startup News–Based Intents
# -----------------------------------------------------------------------------

# 16. TECH_NEWS_QUERY (30 examples)
tech_news_examples = [
    "Show me the latest TechCrunch articles on startups.",
    "Retrieve recent tech news on emerging startups.",
    "What are the latest tech headlines in the startup world?",
    "Give me current TechCrunch news on tech innovations.",
    "Display the latest startup news from TechCrunch.",
    "Show me tech news related to venture capital.",
    "Retrieve recent articles on startup trends from TechCrunch.",
    "What are the new tech developments in the startup ecosystem?",
    "Give me the latest tech updates on emerging companies.",
    "Display recent tech news about startup funding.",
    "Show me current tech headlines on innovative startups.",
    "Retrieve the latest news on startup technology trends.",
    "What are the top TechCrunch articles today?",
    "Give me recent tech news on startup acquisitions.",
    "Show me current TechCrunch articles on tech breakthroughs.",
    "Retrieve the latest startup news and tech updates.",
    "What are the recent tech headlines on disruptive startups?",
    "Display current tech news on startup innovations.",
    "Show me the latest tech news on emerging tech companies.",
    "Retrieve the latest articles on tech trends in startups.",
    "What are the current startup tech updates from TechCrunch?",
    "Give me recent news on tech startups and innovations.",
    "Show me the latest tech articles focusing on startups.",
    "Retrieve current tech news on startup investments.",
    "What are the latest tech headlines regarding startups?",
    "Display recent TechCrunch articles on startup culture.",
    "Show me the newest tech news on emerging startups.",
    "Retrieve the latest updates on tech startups.",
    "What are the top headlines in tech news for startups?",
    "Give me current tech news on startup developments.",
]

# 17. FUNDING_NEWS_QUERY (30 examples)
funding_news_examples = [
    "Show me the latest funding news in the startup world.",
    "Retrieve recent articles about startup funding.",
    "What are the current funding news headlines?",
    "Give me the latest news on startup investments.",
    "Display recent funding news for tech startups.",
    "Show me funding news related to venture capital.",
    "Retrieve the latest articles on startup funding events.",
    "What are the new funding developments in startups?",
    "Give me the latest news on startup funding rounds.",
    "Display recent news about venture funding in startups.",
    "Show me current headlines on startup funding.",
    "Retrieve the latest updates on startup investment news.",
    "What are the latest funding trends in the startup ecosystem?",
    "Give me recent articles on startup capital raises.",
    "Display funding news on innovative tech startups.",
    "Show me current news on startup funding announcements.",
    "Retrieve the latest venture capital funding news.",
    "What are the top headlines in startup funding?",
    "Give me recent news on startup funding activities.",
    "Display the latest funding news for emerging startups.",
    "Show me current updates on startup financing news.",
    "Retrieve the latest news on venture funding for startups.",
    "What are the newest articles on startup funding?",
    "Give me the latest headlines on startup capital investment.",
    "Display recent news on startup funding trends.",
    "Show me current news about startup seed funding.",
    "Retrieve the latest updates on series A funding in startups.",
    "What are the recent headlines on startup funding rounds?",
    "Give me the latest articles on startup funding successes.",
    "Display current funding news in the startup ecosystem.",
]

# 18. EVENT_QUERY (30 examples)
event_query_examples = [
    "Show me upcoming industry events for startups.",
    "List the next tech conferences for startups.",
    "What industry events are happening this month for startups?",
    "Retrieve details on upcoming startup meetups.",
    "Display upcoming conferences in the tech sector.",
    "Show me the latest industry events for tech startups.",
    "What are the next major events in the startup ecosystem?",
    "List upcoming tech events and conferences.",
    "Retrieve details on upcoming startup networking events.",
    "Display upcoming industry meetups for startups.",
    "Show me the schedule for upcoming startup events.",
    "What industry events are on the calendar for tech startups?",
    "List upcoming conferences and events for startups.",
    "Retrieve the latest details on startup expos and events.",
    "Display upcoming events for emerging tech companies.",
    "Show me upcoming startup summits.",
    "What are the next industry events for venture capital?",
    "List upcoming tech summits for startups.",
    "Retrieve details on upcoming events in the startup world.",
    "Display the schedule for upcoming industry conferences.",
    "Show me upcoming startup networking meetups.",
    "What events are scheduled for tech startups this quarter?",
    "List upcoming technology conferences for startups.",
    "Retrieve details on upcoming startup product launches.",
    "Display the latest upcoming events for startups.",
    "Show me upcoming industry events for emerging companies.",
    "What are the next startup forums and expos?",
    "List upcoming events for digital innovation in startups.",
    "Retrieve the schedule for upcoming startup conferences.",
    "Display upcoming networking events for tech startups.",
]

# 19. MARKET_TRENDS_QUERY (30 examples)
market_trends_examples = [
    "Show me current market trends in the startup ecosystem.",
    "What are the latest market trends in tech startups?",
    "Retrieve trends in the venture capital market.",
    "Provide an analysis of current market trends in the tech industry.",
    "Display recent trends in startup funding.",
    "What are the emerging market trends for startups?",
    "Give me an overview of current market trends in digital media.",
    "Show me market trends in the AI startup space.",
    "Retrieve the latest trends in the fintech market.",
    "Provide insights into current market trends in cloud computing.",
    "What are the latest market trends in e-commerce startups?",
    "Display current trends in the cybersecurity market.",
    "Show me trends in the biotech startup ecosystem.",
    "Retrieve insights on market trends for renewable energy startups.",
    "Provide an overview of market trends in edtech.",
    "What are the emerging trends in the IoT market?",
    "Display current trends in the AR/VR startup space.",
    "Show me market trends in the mobile app industry.",
    "Retrieve the latest trends in the gaming industry.",
    "Provide insights into market trends for blockchain startups.",
    "What are the latest market trends in SaaS companies?",
    "Display trends in the digital health startup ecosystem.",
    "Show me current trends in the cloud services market.",
    "Retrieve trends in the enterprise software market.",
    "Provide an analysis of market trends in the social media sector.",
    "What are the emerging trends in the startup investment landscape?",
    "Display current trends in the online retail market.",
    "Show me insights on market trends in digital payments.",
    "Retrieve the latest trends in the startup ecosystem globally.",
    "Provide an overview of market trends in the technology sector.",
]

# -----------------------------------------------------------------------------
# Combine all examples into one training data list
# -----------------------------------------------------------------------------
import random
import csv
import pandas as pd
import itertools

# -------------------------------
# ASSUMPTION: The following example lists are defined.
# For brevity, only the names are referenced here. They should be defined in your module.
#
# company_profile_examples, funding_round_examples, acquisition_examples, ipo_examples,
# investor_query_examples, investment_details_examples, org_relationship_examples,
# investment_partner_examples, funds_query_examples, jobs_query_examples, people_profile_examples,
# education_examples, competitor_lookup_examples, lead_generation_examples, market_analysis_examples,
# tech_news_examples, funding_news_examples, event_query_examples, market_trends_examples
# -------------------------------

# (For this example, we assume these lists are already populated with at least 30 strings each.)

# Create a dictionary mapping each intent to its corresponding example list.
example_data = {
    "COMPANY_PROFILE_QUERY": company_profile_examples,
    "FUNDING_ROUND_QUERY": funding_round_examples,
    "ACQUISITION_QUERY": acquisition_examples,
    "IPO_QUERY": ipo_examples,
    "INVESTOR_QUERY": investor_query_examples,
    "INVESTMENT_DETAILS_QUERY": investment_details_examples,
    "ORGANIZATION_RELATIONSHIP_QUERY": org_relationship_examples,
    "INVESTMENT_PARTNER_QUERY": investment_partner_examples,
    "FUNDS_QUERY": funds_query_examples,
    "JOBS_QUERY": jobs_query_examples,
    "PEOPLE_PROFILE_QUERY": people_profile_examples,
    "EDUCATION_QUERY": education_examples,
    "COMPETITOR_LOOKUP": competitor_lookup_examples,
    "LEAD_GENERATION_QUERY": lead_generation_examples,
    "MARKET_ANALYSIS_QUERY": market_analysis_examples,
    "TECH_NEWS_QUERY": tech_news_examples,
    "FUNDING_NEWS_QUERY": funding_news_examples,
    "EVENT_QUERY": event_query_examples,
    "MARKET_TRENDS_QUERY": market_trends_examples,
}

# # List of all intents (for later use)
# INTENTS = list(example_data.keys())

# def multi_cat_dict(active_intents):
#     """
#     Returns a dictionary mapping each intent to 1.0 if present in active_intents, else 0.0.
#     """
#     return {intent: 1.0 if intent in active_intents else 0.0 for intent in INTENTS}

# def generate_random_multilabel_example():
#     """
#     Randomly selects between 2 and 4 intents, picks one example per selected intent,
#     and combines them into a single query string.
#     Returns:
#         combined_query (str): The combined query text.
#         selected_intents (list): The list of intents corresponding to the selected examples.
#     """
#     num_intents = random.choice([2, 3, 4])
#     selected_intents = random.sample(INTENTS, num_intents)
#     selected_examples = [random.choice(example_data[intent]).strip() for intent in selected_intents]
#     combined_query = " ".join(selected_examples)
#     return combined_query, selected_intents

# # -------------------------------
# # PART 1: Generate CSV with Single-Label and Multi-Label Examples
# # -------------------------------

combined_rows = []

# 1. Add single-label examples: for each intent, add each example from its list.
for intent, examples in example_data.items():
    for query in examples:
        row = {
            "query": query.strip(),
            "labels": intent,            # single label
            "example_type": "single"
        }
        combined_rows.append(row)

# # 2. Add multi-label examples: generate a desired number of random combinations.
# num_multi_examples = 10000  # adjust as needed
# for _ in range(num_multi_examples):
#     query, intents = generate_random_multilabel_example()
#     row = {
#         "query": query,
#         "labels": ",".join(intents),  # comma-separated list of labels
#         "example_type": "multi"
#     }
#     combined_rows.append(row)

# # Write combined examples to CSV.
# output_csv = "combined_training_data.csv"
# with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
#     fieldnames = ["query", "labels", "example_type"]
#     writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
#     writer.writeheader()
#     for row in combined_rows:
#         writer.writerow(row)

# print(f"Combined training data saved to '{output_csv}' with {len(combined_rows)} examples.")

# List of all intents (keys of example_data)
INTENTS = list(example_data.keys())

# Number of examples to take per combination (if available)
num_examples_per_combination = 3

# combined_rows = []

# ---------------------------
# Part 1: Two-intent (Pair) Combinations
# ---------------------------
for intent_pair in itertools.combinations(INTENTS, 2):
    list1 = example_data[intent_pair[0]]
    list2 = example_data[intent_pair[1]]
    # Limit the number of combined examples by taking the first num_examples_per_combination examples from each list (if available)
    num_samples = min(num_examples_per_combination, len(list1), len(list2))
    for i in range(num_samples):
        combined_query = list1[i].strip() + " " + list2[i].strip()
        combined_rows.append({
            "query": combined_query,
            "labels": ",".join(intent_pair),
            "example_type": "pair"
        })

# ---------------------------
# Part 2: Three-intent (Triple) Combinations
# ---------------------------
for intent_triplet in itertools.combinations(INTENTS, 3):
    list1 = example_data[intent_triplet[0]]
    list2 = example_data[intent_triplet[1]]
    list3 = example_data[intent_triplet[2]]
    num_samples = min(num_examples_per_combination, len(list1), len(list2), len(list3))
    for i in range(num_samples):
        combined_query = (
            list1[i].strip() + " " +
            list2[i].strip() + " " +
            list3[i].strip()
        )
        combined_rows.append({
            "query": combined_query,
            "labels": ",".join(intent_triplet),
            "example_type": "triple"
        })

# ---------------------------
# Write the combined training data to CSV.
# ---------------------------
output_csv = "systematic_multilabel_training_data.csv"
with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
    fieldnames = ["query", "labels", "example_type"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for row in combined_rows:
        writer.writerow(row)

print(f"Systematic multi-label training data saved to '{output_csv}' with {len(combined_rows)} examples.")


# -------------------------------
# PART 2: Augment Data by Paraphrasing (Using nlpaug)
# -------------------------------
try:
    from nlpaug.augmenter.word import ContextualWordEmbsAug
except ImportError:
    print("Please install nlpaug (pip install nlpaug) to use the augmentation feature.")
    raise

# Create a paraphrasing augmenter (using a contextual word embeddings model).
# (You can adjust parameters as needed.)
augmenter = ContextualWordEmbsAug(
    model_path='bert-base-uncased',  # you can choose another model if desired
    action="substitute",
    device='cpu'  # change to 'cuda' if you have a GPU available
)

# Load the generated CSV into a DataFrame.
df = pd.read_csv(output_csv)

# Define how many augmented sentences to generate per original sentence.
num_augmented_per_query = 3

augmented_rows = []

# For each row in the CSV, generate augmented (paraphrased) queries.
for i, row in df.iterrows():
    original_query = row["query"]
    labels = row["labels"]
    example_type = row["example_type"]
    print(f"Augmenting query: ",i)
    
    # Generate augmented versions (if augmentation fails, we can fallback to the original)
    try:
        aug_queries = augmenter.augment(original_query, n=num_augmented_per_query)
    except Exception as e:
        print(f"Augmentation error for query '{original_query}': {e}")
        aug_queries = [original_query]  # fallback
    
    # For each augmented query, add a new row.
    for aug_query in aug_queries:
        augmented_rows.append({
            "query": aug_query,
            "labels": labels,
            "example_type": example_type,
            "augmented": True
        })

# Also add the original rows (mark them as not augmented).
for _, row in df.iterrows():
    row_dict = row.to_dict()
    row_dict["augmented"] = False
    augmented_rows.append(row_dict)

# Save the augmented data to a new CSV file.
augmented_csv = "augmented_training_data.csv"
df_aug = pd.DataFrame(augmented_rows)
df_aug.to_csv(augmented_csv, index=False, encoding="utf-8")

print(f"Augmented training data (original + paraphrased) saved to '{augmented_csv}'.")

