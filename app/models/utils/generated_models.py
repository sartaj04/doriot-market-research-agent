from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date
from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION
from sqlalchemy.orm import relationship
from core.database import Base

class Companies(Base):
    __tablename__ = 'companies'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    legal_name = Column(Text)
    roles = Column(Text)
    domain = Column(Text)
    homepage_url = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    address = Column(Text)
    postal_code = Column(Text)
    status = Column(Text)
    short_description = Column(Text)
    category_list = Column(Text)
    category_groups_list = Column(Text)
    num_funding_rounds = Column(DOUBLE_PRECISION)
    total_funding_usd = Column(DOUBLE_PRECISION)
    total_funding = Column(DOUBLE_PRECISION)
    total_funding_currency_code = Column(Text)
    founded_on = Column(Text)
    last_funding_on = Column(Text)
    closed_on = Column(Text)
    employee_count = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    facebook_url = Column(Text)
    linkedin_url = Column(Text)
    twitter_url = Column(Text)
    logo_url = Column(Text)
    alias1 = Column(Text)
    alias2 = Column(Text)
    alias3 = Column(Text)
    primary_role = Column(Text)
    num_exits = Column(DOUBLE_PRECISION)


class OrganizationDescriptions(Base):
    __tablename__ = 'organization_descriptions'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    description = Column(Text)


class CategoryGroups(Base):
    __tablename__ = 'category_groups'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    category_groups_list = Column(Text)


class People(Base):
    __tablename__ = 'people'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    first_name = Column(Text)
    last_name = Column(Text)
    gender = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    featured_job_organization_uuid = Column(Text)
    featured_job_organization_name = Column(Text)
    featured_job_title = Column(Text)
    facebook_url = Column(Text)
    linkedin_url = Column(Text)
    twitter_url = Column(Text)
    logo_url = Column(Text)


class PeopleDescriptions(Base):
    __tablename__ = 'people_descriptions'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    description = Column(Text)


class Degrees(Base):
    __tablename__ = 'degrees'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(DOUBLE_PRECISION)
    cb_url = Column(DOUBLE_PRECISION)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    person_uuid = Column(Text)
    person_name = Column(Text)
    institution_uuid = Column(Text)
    institution_name = Column(Text)
    degree_type = Column(Text)
    subject = Column(Text)
    started_on = Column(Text)
    completed_on = Column(Text)
    is_completed = Column(Boolean)


class Jobs(Base):
    __tablename__ = 'jobs'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    person_uuid = Column(Text)
    person_name = Column(Text)
    org_uuid = Column(Text)
    org_name = Column(Text)
    started_on = Column(Text)
    ended_on = Column(Text)
    is_current = Column(Boolean)
    title = Column(Text)
    job_type = Column(Text)


class Investors(Base):
    __tablename__ = 'investors'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    roles = Column(Text)
    domain = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    investor_types = Column(Text)
    investment_count = Column(DOUBLE_PRECISION)
    total_funding_usd = Column(DOUBLE_PRECISION)
    total_funding = Column(DOUBLE_PRECISION)
    total_funding_currency_code = Column(Text)
    founded_on = Column(Text)
    closed_on = Column(Text)
    facebook_url = Column(Text)
    linkedin_url = Column(Text)
    twitter_url = Column(Text)
    logo_url = Column(Text)


class Investments(Base):
    __tablename__ = 'investments'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    funding_round_uuid = Column(Text)
    funding_round_name = Column(Text)
    investor_uuid = Column(Text)
    investor_name = Column(Text)
    investor_type = Column(Text)
    is_lead_investor = Column(Boolean)


class Funds(Base):
    __tablename__ = 'funds'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    entity_uuid = Column(Text)
    entity_name = Column(Text)
    entity_type = Column(Text)
    announced_on = Column(Text)
    raised_amount_usd = Column(DOUBLE_PRECISION)
    raised_amount = Column(DOUBLE_PRECISION)
    raised_amount_currency_code = Column(Text)


class FundingRounds(Base):
    __tablename__ = 'funding_rounds'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    investment_type = Column(Text)
    announced_on = Column(Text)
    raised_amount_usd = Column(DOUBLE_PRECISION)
    raised_amount = Column(DOUBLE_PRECISION)
    raised_amount_currency_code = Column(Text)
    post_money_valuation_usd = Column(DOUBLE_PRECISION)
    post_money_valuation = Column(DOUBLE_PRECISION)
    post_money_valuation_currency_code = Column(Text)
    investor_count = Column(DOUBLE_PRECISION)
    org_uuid = Column(Text)
    org_name = Column(Text)
    lead_investor_uuids = Column(Text)


class Ipos(Base):
    __tablename__ = 'ipos'

    uuid = Column(Text)
    name = Column(DOUBLE_PRECISION)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    org_uuid = Column(Text)
    org_name = Column(Text)
    org_cb_url = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    stock_exchange_symbol = Column(Text)
    stock_symbol = Column(Text)
    went_public_on = Column(Text)
    share_price_usd = Column(DOUBLE_PRECISION)
    share_price = Column(DOUBLE_PRECISION)
    share_price_currency_code = Column(Text)
    valuation_price_usd = Column(DOUBLE_PRECISION)
    valuation_price = Column(DOUBLE_PRECISION)
    valuation_price_currency_code = Column(Text)
    money_raised_usd = Column(DOUBLE_PRECISION)
    money_raised = Column(DOUBLE_PRECISION)
    money_raised_currency_code = Column(Text)


class Acquisitions(Base):
    __tablename__ = 'acquisitions'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    acquiree_uuid = Column(Text)
    acquiree_name = Column(Text)
    acquiree_cb_url = Column(Text)
    acquiree_country_code = Column(Text)
    acquiree_state_code = Column(Text)
    acquiree_region = Column(Text)
    acquiree_city = Column(Text)
    acquirer_uuid = Column(Text)
    acquirer_name = Column(Text)
    acquirer_cb_url = Column(Text)
    acquirer_country_code = Column(Text)
    acquirer_state_code = Column(Text)
    acquirer_region = Column(Text)
    acquirer_city = Column(Text)
    acquisition_type = Column(Text)
    acquired_on = Column(Text)
    price_usd = Column(DOUBLE_PRECISION)
    price = Column(DOUBLE_PRECISION)
    price_currency_code = Column(Text)


class Events(Base):
    __tablename__ = 'events'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    short_description = Column(Text)
    started_on = Column(Text)
    ended_on = Column(Text)
    event_url = Column(Text)
    registration_url = Column(Text)
    venue_name = Column(Text)
    description = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    logo_url = Column(Text)
    event_roles = Column(Text)


class EventAppearances(Base):
    __tablename__ = 'event_appearances'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    event_uuid = Column(Text)
    event_name = Column(Text)
    participant_uuid = Column(Text)
    participant_name = Column(Text)
    participant_type = Column(Text)
    appearance_type = Column(Text)
    short_description = Column(Text)


class TechcrunchVentureArticles(Base):
    __tablename__ = 'techcrunch_venture_articles'

    id = Column(INTEGER)
    title = Column(Text)
    url = Column(Text)
    published_at = Column(TIMESTAMP)
    author = Column(Text)
    category = Column(Text)
    article_text = Column(Text)
    article_html = Column(Text)


class OrgParents(Base):
    __tablename__ = 'org_parents'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    parent_uuid = Column(Text)
    parent_name = Column(Text)


class InvestmentPartners(Base):
    __tablename__ = 'investment_partners'

    uuid = Column(Text)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    funding_round_uuid = Column(Text)
    funding_round_name = Column(Text)
    investor_uuid = Column(Text)
    investor_name = Column(Text)
    partner_uuid = Column(Text)
    partner_name = Column(Text)


class FundingNews(Base):
    __tablename__ = 'funding_news'

    id = Column(INTEGER)
    title = Column(Text)
    url = Column(Text)
    source = Column(Text)
    published_at = Column(Date)
    content = Column(Text)


class TechcrunchStartupArticles(Base):
    __tablename__ = 'techcrunch_startup_articles'

    id = Column(INTEGER)
    title = Column(Text)
    url = Column(Text)
    published_at = Column(TIMESTAMP)
    author = Column(Text)
    category = Column(Text)
    article_text = Column(Text)
    article_html = Column(Text)


