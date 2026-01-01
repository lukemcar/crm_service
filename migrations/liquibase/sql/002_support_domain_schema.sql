-- ======================================================================
-- Dyno CRM – SUPPORT / HELPDESK DOMAIN (Zendesk-like, AI-first via dyno_ai)
-- ======================================================================
-- liquibase formatted sql
-- changeset crm_service:002_support_domain_schema
--
-- PURPOSE
--   Zendesk-like support domain for Dyno CRM.
--   - Tickets, message threads, attachments
--   - Assignment, audit timeline, participants/watchers
--   - SLA definitions + per-ticket SLA state
--   - Views + macros (support UI convenience)
--   - Optional: custom fields/forms, CSAT, KB, time tracking, metrics
--
-- KEY ARCHITECTURE DECISIONS
--   1) Tenant Service is source-of-truth for tenants/users/roles/groups.
--      CRM stores shadow projections so it can:
--        - enforce tenant-safe foreign keys (assignment integrity)
--        - support fast joins for UI/reporting
--        - avoid calling tenant service for every query
--
--   2) "Support queues" are NOT a separate group object in CRM.
--      A queue is a Tenant Service group with a CRM-local support profile:
--        - tenant_group_shadow = "the group exists"
--        - group_profile(profile_type='support_queue') = "this group is a support queue"
--
--   3) Orchestration (Flowable) is system-of-record for automation and task execution.
--      CRM mirrors task state for UI in ticket_task_mirror.
--
--   4) AI Workforce Service (dyno_ai / ai_workforce_service) is system-of-record for AI runs.
--      CRM stores only:
--        - lightweight pointers and status on tickets (ai_last_session_id, ai_status, etc.)
--        - ticket_ai_work_ref rows for history/UX linking (no detailed run logs here)
--
-- SECURITY / TENANCY
--   - All domain tables are tenant scoped via tenant_id.
--   - Composite foreign keys enforce tenant consistency.
--   - Secrets for channels/integrations must NOT be stored here.
--     Store secrets in a secrets manager and/or integration service.
--
-- ======================================================================

SET search_path TO public, dyno_crm;

-- ----------------------------------------------------------------------
-- TENANT SERVICE SHADOW PROJECTIONS (CRM-local read models)
-- ----------------------------------------------------------------------
-- These tables are projections ONLY. Do not treat them as source-of-truth.
-- Populated ONLY by events from the Tenant Service.
-- CRM uses them to enforce tenant-safe foreign keys for assignment, display
-- user and group names in the UI, and join efficiently without hitting the
-- Tenant Service. They are not editable within CRM.

-- 
-- Table: tenant_user_shadow
-- Domain object: Projection of a user from the Tenant Service.
-- Description:
--   This table stores a shadow copy of each active user per tenant.  Each
--   row represents a user known to the tenant.  It includes display fields
--   such as display_name and email for convenience in the CRM UI.
-- Usage in the system:
--   - Used to populate assignment drop-downs when assigning tickets to agents.
--   - Used to display agent names in ticket lists, messages, and audit logs.
--   - Enforces tenant-scoped foreign keys for user assignments (assigned_user_id).
--   - Not editable by CRM; updated via events from the Tenant Service.
-- Integration:
--   - Populated/updated/deleted asynchronously by listening to user events
--     from the Tenant Service.
--   - It does not store sensitive data; only basic identifying info.
CREATE TABLE IF NOT EXISTS dyno_crm.tenant_user_shadow (
    tenant_id UUID NOT NULL,
    user_id   UUID NOT NULL,

    display_name VARCHAR(255),
    email        VARCHAR(320),
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_tenant_user_shadow PRIMARY KEY (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS ix_tenant_user_shadow_tenant
    ON dyno_crm.tenant_user_shadow(tenant_id);

CREATE INDEX IF NOT EXISTS ix_tenant_user_shadow_tenant_email
    ON dyno_crm.tenant_user_shadow(tenant_id, lower(email))
    WHERE email IS NOT NULL;

-- 
-- Table: tenant_group_shadow
-- Domain object: Projection of groups from the Tenant Service.
-- Description:
--   This table contains a row for every group defined in the Tenant Service
--   for a given tenant.  The CRM does not create or own groups itself; it
--   simply mirrors them so that tickets can be assigned to groups and the UI
--   can show group names.  group_key is a stable identifier used by
--   orchestration (Flowable) for candidate group assignment and is optional.
-- Usage in the system:
--   - Primary lookup for group names and IDs when assigning tickets to queues.
--   - Joins with group_profile to determine whether a group functions as a
--     support queue (profile_type='support_queue') and to apply default SLA and AI posture.
--   - Used by ticket_list filters and reporting to group tickets by queue.
--   - Not editable by CRM; updated via Tenant Service events.
-- Integration:
--   - Populated/updated via events from the Tenant Service.
--   - Provides stable group IDs/keys for Orchestration candidateGroups in
--     Flowable process definitions.
CREATE TABLE IF NOT EXISTS dyno_crm.tenant_group_shadow (
    id UUID PRIMARY KEY,          -- mirrors Tenant Service group_id
    tenant_id UUID NOT NULL,

    group_name VARCHAR(255) NOT NULL,
    group_key  VARCHAR(100),      -- stable key recommended (great for Flowable candidateGroups)
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ux_tenant_group_shadow_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_tenant_group_shadow_tenant_name
    ON dyno_crm.tenant_group_shadow(tenant_id, group_name);

CREATE INDEX IF NOT EXISTS ix_tenant_group_shadow_tenant
    ON dyno_crm.tenant_group_shadow(tenant_id);

CREATE INDEX IF NOT EXISTS ix_tenant_group_shadow_tenant_group_key
    ON dyno_crm.tenant_group_shadow(tenant_id, group_key)
    WHERE group_key IS NOT NULL;

-- ----------------------------------------------------------------------
-- GROUP PROFILE (Support queue specialization)
-- ----------------------------------------------------------------------
-- Domain object: CRM-local metadata that defines how a group is used
--   within the support module.
-- Description:
--   While group identities come from the Tenant Service, CRM needs to know
--   which groups are support queues, sales teams, or other roles.  The
--   group_profile table attaches a profile to each mirrored group.  For
--   support_queue profiles, it also defines default behaviors such as the
--   default SLA policy, routing configuration, and AI work mode.  This
--   decouples group definitions from support-specific settings.
-- Usage in the system:
--   - Admin UI: manage support queues by toggling is_support_queue and
--     is_assignable flags, set default SLA policy and AI mode.
--   - Ticket assignment: when a ticket is assigned to a queue, UI and
--     orchestration consult group_profile to determine if AI is allowed and
--     which SLA policy to apply by default.
--   - Filtering: group_profile.profile_type can be used to separate support
--     queues from sales groups or security-only groups.
--   - Does not duplicate group records; group_id references
--     tenant_group_shadow.id.
-- Integration:
--   - Links to sla_policy for default SLA.
--   - ai_work_mode_default influences whether tickets assigned to this queue
--     are queued for AI processing via dyno_ai.
CREATE TABLE IF NOT EXISTS dyno_crm.group_profile (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    group_id UUID NOT NULL,  -- tenant_group_shadow.id

    profile_type VARCHAR(50) NOT NULL DEFAULT 'support_queue',
    is_support_queue BOOLEAN NOT NULL DEFAULT TRUE,
    is_assignable  BOOLEAN NOT NULL DEFAULT TRUE,

    -- Optional support queue defaults
    default_sla_policy_id UUID,          -- FK added after sla_policy is created
    routing_config JSONB,                -- skills/tags/keywords/priority mapping (non-secret)

    -- Default AI posture for tickets assigned to this queue.
    ai_work_mode_default VARCHAR(50) NOT NULL DEFAULT 'human_only',

    -- Placeholder if you later add business hours domain in CRM (or reference orchestration calendars)
    business_hours_id UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_group_profile_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_group_profile_group
        FOREIGN KEY (group_id) REFERENCES tenant_group_shadow(id) ON DELETE CASCADE,

    CONSTRAINT fk_group_profile_group_tenant
        FOREIGN KEY (group_id, tenant_id) REFERENCES tenant_group_shadow(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_group_profile_type
        CHECK (profile_type IN ('support_queue','sales_team','security_only','generic')),

    CONSTRAINT ck_group_profile_ai_work_mode_default
        CHECK (ai_work_mode_default IN ('human_only','ai_allowed','ai_preferred','ai_only'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_group_profile_unique_by_group
    ON dyno_crm.group_profile(tenant_id, group_id);

CREATE INDEX IF NOT EXISTS ix_group_profile_tenant_type
    ON dyno_crm.group_profile(tenant_id, profile_type);

CREATE INDEX IF NOT EXISTS ix_group_profile_tenant_support_queue
    ON dyno_crm.group_profile(tenant_id, is_support_queue)
    WHERE is_support_queue = TRUE;

-- ----------------------------------------------------------------------
-- INBOUND CHANNEL (email inbox, sms number, chat widget, etc.)
-- ----------------------------------------------------------------------
-- Domain object: Describes an entry point for inbound messages that can
--   generate tickets or add messages to existing tickets.
-- Description:
--   Each inbound_channel row represents a unique inbox or integration.  The
--   channel_type identifies the channel (e.g. email, web, chat, SMS), name
--   is a friendly label for the admin UI, external_ref stores the provider
--   identifier (like mailbox id or phone number id), and config holds
--   non-secret configuration details (e.g. reply-to address for web forms).
--   Only non-secret data should be stored here; secrets should live in a
--   secure integration service or secrets manager.
-- Usage in the system:
--   - Admin UI: configure inbound channels, name them, set channel type and
--     provider references.  Enable/disable channels via is_active.
--   - Ticket creation: when an inbound event arrives, CRM uses
--     inbound_channel to look up the channel id from external_ref and set
--     inbound_channel_id on the ticket.
--   - Filtering: support staff can filter tickets by channel.
-- Integration:
--   - External services (email servers, chat providers, SMS gateways) send
--     inbound events with provider identifiers (external_ref).  CRM
--     matches them to inbound_channel entries.
--   - Outbound replies may use config to send messages via the correct
--     provider.
CREATE TABLE IF NOT EXISTS dyno_crm.inbound_channel (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    channel_type VARCHAR(50) NOT NULL,      -- email|web|chat|sms|voice|api|internal|social
    name VARCHAR(255) NOT NULL,
    external_ref VARCHAR(255),              -- inbox-id, phone-number-id, page-id, etc.
    config JSONB,                           -- non-secret provider config
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_inbound_channel_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT ck_inbound_channel_type
        CHECK (channel_type IN ('email','web','chat','sms','voice','api','internal','social'))
);

CREATE INDEX IF NOT EXISTS ix_inbound_channel_tenant
    ON dyno_crm.inbound_channel(tenant_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_inbound_channel_tenant_external_ref
    ON dyno_crm.inbound_channel(tenant_id, channel_type, external_ref)
    WHERE external_ref IS NOT NULL;

-- ----------------------------------------------------------------------
-- TICKET (core case)
-- ----------------------------------------------------------------------
-- Domain object: The durable unit of work representing a support case.
-- Description:
--   The ticket table captures the high-level properties of a customer
--   request or incident.  Each ticket belongs to a tenant and references
--   the requester contact (customer), optional company (organization), and
--   inbound channel that created it.  Ticket fields capture its status,
--   priority, type, assignment (group/user), timestamps for service level
--   measurement, custom fields via JSONB, and orchestration linkages.
--   AI posture fields describe whether an AI agent may work on the ticket and
--   track last AI session outcome.  The ticket does not store the message
--   conversation itself; the conversation is stored in ticket_message.
-- Usage in the system:
--   - Support UI: list and view tickets, filter by status/priority/type,
--     assign to queues or agents, view and update status, priority, type, and
--     custom fields.  Update description for initial body or use first
--     ticket_message as body.  The UI shows assignment options based on
--     tenant_user_shadow and tenant_group_shadow.
--   - AI integration: work_mode, ai_status, and ai_last_* fields allow the UI
--     to indicate AI processing state and link to dyno_ai sessions.  The
--     system will publish work requests to dyno_ai based on work_mode and
--     queue settings.
--   - Orchestration integration: tickets can optionally be linked to a
--     Flowable workflow instance via orchestration_workflow_key and
--     orchestration_instance_id; CRM mirrors Flowable tasks via
--     ticket_task_mirror.
--   - SLA integration: group_profile may define a default SLA policy; the
--     ticket_sla_state stores computed SLA deadlines/breaches.
-- Integration:
--   - References to contact, company, inbound_channel, tenant_group_shadow,
--     tenant_user_shadow enforce tenant-safe assignments.
--   - AI integration via dyno_ai: the ai_last_session_id points to the last
--     AI session for this ticket; ai_last_agent_key identifies the agent used.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    -- Customer identity context (CRM-owned)
    requester_contact_id UUID,
    company_id UUID,

    -- Channel / entry point
    inbound_channel_id UUID,

    -- Optional form selection for custom fields
    ticket_form_id UUID,

    subject VARCHAR(255) NOT NULL,
    description TEXT,                      -- initial body (first message may also be stored in ticket_message)

    status VARCHAR(50) NOT NULL DEFAULT 'new',
    priority VARCHAR(50) NOT NULL DEFAULT 'normal',
    ticket_type VARCHAR(50) NOT NULL DEFAULT 'question',

    -- Assignment targets (Tenant Service projections)
    assigned_group_id UUID,                -- tenant_group_shadow.id
    assigned_user_id UUID,                 -- tenant_user_shadow.user_id (via (tenant_id,user_id))

    -- Support timestamps
    first_response_at TIMESTAMPTZ,
    last_message_at TIMESTAMPTZ,
    solved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,

    -- Extensibility
    custom_fields JSONB,

    -- Orchestration linkage (Flowable)
    orchestration_workflow_key VARCHAR(255),
    orchestration_instance_id VARCHAR(128),
    orchestration_state JSONB,

    -- AI posture (execution is in dyno_ai; these are UI/routing hints + last-known state)
    work_mode VARCHAR(50) NOT NULL DEFAULT 'human_only',   -- human_only|ai_allowed|ai_preferred|ai_only
    ai_status VARCHAR(50) NOT NULL DEFAULT 'idle',         -- idle|queued|working|waiting_for_human|blocked|completed|failed

    -- Pointer to the LAST AI Workforce session that acted on this ticket (dyno_ai.work_session.id)
    ai_last_session_id UUID,
    ai_last_agent_key VARCHAR(120),        -- e.g., 'support_ticket_triage'
    ai_last_outcome VARCHAR(50),           -- success|partial|failed|canceled
    ai_last_confidence NUMERIC(5,4),
    ai_last_completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_ticket_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_requester_contact
        FOREIGN KEY (requester_contact_id) REFERENCES contact(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_requester_contact_tenant
        FOREIGN KEY (requester_contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_company
        FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_company_tenant
        FOREIGN KEY (company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_inbound_channel
        FOREIGN KEY (inbound_channel_id) REFERENCES inbound_channel(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_inbound_channel_tenant
        FOREIGN KEY (inbound_channel_id, tenant_id) REFERENCES inbound_channel(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_assigned_group
        FOREIGN KEY (assigned_group_id) REFERENCES tenant_group_shadow(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_assigned_group_tenant
        FOREIGN KEY (assigned_group_id, tenant_id) REFERENCES tenant_group_shadow(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_assigned_user_tenant
        FOREIGN KEY (tenant_id, assigned_user_id) REFERENCES tenant_user_shadow(tenant_id, user_id) ON DELETE SET NULL,

    CONSTRAINT ck_ticket_status
        CHECK (status IN ('new','open','pending','on_hold','solved','closed')),

    CONSTRAINT ck_ticket_priority
        CHECK (priority IN ('low','normal','high','urgent')),

    CONSTRAINT ck_ticket_type
        CHECK (ticket_type IN ('question','incident','problem','task')),

    CONSTRAINT ck_ticket_work_mode
        CHECK (work_mode IN ('human_only','ai_allowed','ai_preferred','ai_only')),

    CONSTRAINT ck_ticket_ai_status
        CHECK (ai_status IN ('idle','queued','working','waiting_for_human','blocked','completed','failed')),

    CONSTRAINT ck_ticket_ai_outcome
        CHECK (ai_last_outcome IS NULL OR ai_last_outcome IN ('success','partial','failed','canceled'))
);

CREATE INDEX IF NOT EXISTS ix_ticket_tenant
    ON dyno_crm.ticket(tenant_id);

CREATE INDEX IF NOT EXISTS ix_ticket_tenant_status
    ON dyno_crm.ticket(tenant_id, status);

CREATE INDEX IF NOT EXISTS ix_ticket_tenant_priority
    ON dyno_crm.ticket(tenant_id, priority);

CREATE INDEX IF NOT EXISTS ix_ticket_tenant_assigned_user
    ON dyno_crm.ticket(tenant_id, assigned_user_id)
    WHERE assigned_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_ticket_tenant_assigned_group
    ON dyno_crm.ticket(tenant_id, assigned_group_id)
    WHERE assigned_group_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_ticket_tenant_requester
    ON dyno_crm.ticket(tenant_id, requester_contact_id)
    WHERE requester_contact_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_ticket_tenant_company
    ON dyno_crm.ticket(tenant_id, company_id)
    WHERE company_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_ticket_tenant_last_message
    ON dyno_crm.ticket(tenant_id, last_message_at DESC);

CREATE INDEX IF NOT EXISTS ix_ticket_tenant_ai_status
    ON dyno_crm.ticket(tenant_id, ai_status);

-- ----------------------------------------------------------------------
-- TICKET PARTICIPANTS (CCs / followers / watchers)
-- ----------------------------------------------------------------------
-- Domain object: Represents people who are subscribed to updates on a ticket.
-- Description:
--   In addition to the requester and assignee(s), tickets may have other
--   participants who need to be kept in the loop.  This table stores
--   references to contacts and agents who are watching a ticket.  The role
--   column distinguishes requester (the original contact), cc, or follower.
-- Usage in the system:
--   - UI: display participants list on the ticket detail page, allow agents
--     to add/remove CCs and followers.
--   - Notification engine: deliver update notifications to all participants
--     based on their role and preferences.
--   - Assignment logic: a requester (participant_type='contact' and role='requester')
--     may be set for each ticket.
-- Integration:
--   - References contact and tenant_user_shadow to ensure tenant-safe
--     associations.
--   - Participants may receive email/SMS notifications via integration
--     services, but the details are handled outside this table.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_participant (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    ticket_id UUID NOT NULL,

    participant_type VARCHAR(50) NOT NULL,  -- contact|agent
    contact_id UUID,
    user_id UUID,                           -- tenant_user_shadow.user_id

    role VARCHAR(50) NOT NULL DEFAULT 'cc', -- requester|cc|follower

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_participant_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_participant_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_participant_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_participant_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_participant_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_participant_user_tenant
        FOREIGN KEY (tenant_id, user_id) REFERENCES tenant_user_shadow(tenant_id, user_id) ON DELETE SET NULL,

    CONSTRAINT ck_ticket_participant_type
        CHECK (participant_type IN ('contact','agent')),

    CONSTRAINT ck_ticket_participant_role
        CHECK (role IN ('requester','cc','follower'))
);

CREATE INDEX IF NOT EXISTS ix_ticket_participant_tenant_ticket
    ON dyno_crm.ticket_participant(tenant_id, ticket_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_participant_unique_contact
    ON dyno_crm.ticket_participant(tenant_id, ticket_id, contact_id, role)
    WHERE contact_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_participant_unique_user
    ON dyno_crm.ticket_participant(tenant_id, ticket_id, user_id, role)
    WHERE user_id IS NOT NULL;

-- ----------------------------------------------------------------------
-- TICKET TAG (query-friendly tags)
-- ----------------------------------------------------------------------
-- Domain object: Tagging system for tickets.
-- Description:
--   Tags are simple strings that can be attached to tickets for flexible
--   categorization.  They support case-insensitive uniqueness per ticket.
-- Usage in the system:
--   - UI: add/remove tags on tickets; filter and search by tag across
--     tickets.  Display tags in ticket lists and details.
--   - Analytics: tags can drive reporting and routing.
-- Integration:
--   - Tags are local to CRM; no external integration.  However, AI
--     workflows may set or read tags as part of triage.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_tag (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    ticket_id UUID NOT NULL,

    tag VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_tag_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_tag_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_tag_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_tag_unique
    ON dyno_crm.ticket_tag(tenant_id, ticket_id, lower(tag));

CREATE INDEX IF NOT EXISTS ix_ticket_tag_tenant_tag
    ON dyno_crm.ticket_tag(tenant_id, lower(tag));

-- ----------------------------------------------------------------------
-- TICKET MESSAGE (append-only thread)
-- ----------------------------------------------------------------------
-- Domain object: Conversation thread of a ticket.
-- Description:
--   Each record in ticket_message is a single message or note in the
--   conversation associated with a ticket.  Messages are append-only (no
--   updates or deletions) to preserve history.  author_type distinguishes
--   between contact messages, agent messages, system-generated messages, and
--   AI-generated messages.  channel_type records which channel the message
--   originated from.  is_public distinguishes between public messages (sent to
--   the requester) and internal notes (agent-only).  external_ref stores an
--   idempotency key from the provider (like email message-id) to avoid
--   duplicate ingestion.  metadata holds provider payload snapshots (non-secret).
-- Usage in the system:
--   - UI: display the conversation thread in chronological order, with
--     different styling for public vs internal messages and for agent vs
--     customer messages.  Show author names using author_display_name or
--     look up contact/user as appropriate.
--   - Notifications: new messages trigger notifications to participants
--     depending on is_public and participant preferences.
--   - AI integration: AI replies are stored as messages with author_type='ai'.
-- Integration:
--   - Channel integrations use external_ref and channel_type to deduplicate and
--     identify messages across systems (e.g. email providers).
--   - Orchestration may produce system messages (status changes, SLA events).
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_message (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    ticket_id UUID NOT NULL,

    author_type VARCHAR(50) NOT NULL,      -- contact|agent|system|ai
    author_contact_id UUID,
    author_user_id UUID,                   -- tenant_user_shadow.user_id
    author_display_name VARCHAR(255),

    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    channel_type VARCHAR(50) NOT NULL DEFAULT 'internal', -- email|web|chat|sms|voice|api|internal|social
    external_ref VARCHAR(255),

    subject VARCHAR(255),
    body TEXT NOT NULL,

    metadata JSONB,                        -- provider payload snapshot (non-secret)

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_message_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_message_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_message_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_message_author_contact
        FOREIGN KEY (author_contact_id) REFERENCES contact(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_message_author_contact_tenant
        FOREIGN KEY (author_contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_message_author_user_tenant
        FOREIGN KEY (tenant_id, author_user_id) REFERENCES tenant_user_shadow(tenant_id, user_id) ON DELETE SET NULL,

    CONSTRAINT ck_ticket_message_author_type
        CHECK (author_type IN ('contact','agent','system','ai')),

    CONSTRAINT ck_ticket_message_channel_type
        CHECK (channel_type IN ('email','web','chat','sms','voice','api','internal','social'))
);

CREATE INDEX IF NOT EXISTS ix_ticket_message_tenant_ticket_created
    ON dyno_crm.ticket_message(tenant_id, ticket_id, created_at ASC);

CREATE INDEX IF NOT EXISTS ix_ticket_message_tenant_created
    ON dyno_crm.ticket_message(tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_ticket_message_tenant_external_ref
    ON dyno_crm.ticket_message(tenant_id, channel_type, external_ref)
    WHERE external_ref IS NOT NULL;

-- ----------------------------------------------------------------------
-- TICKET ATTACHMENT
-- ----------------------------------------------------------------------
-- Domain object: Attachments associated with tickets or messages.
-- Description:
--   Attachments represent files uploaded by customers or agents and linked
--   either to a specific message (ticket_message_id) or directly to the
--   ticket if not tied to a particular message.  The storage_provider and
--   storage_key identify where the file is stored (e.g. S3, GCS), while
--   file_name, content_type, size, and checksum provide metadata.  CRM does
--   not store the file itself, just a pointer and metadata.
-- Usage in the system:
--   - UI: display attachments list under messages and tickets; allow
--     download of file via storage key and provider.
--   - Deduplication: file checksum may be used to detect duplicates.
-- Integration:
--   - File storage services: the storage_provider and storage_key map to an
--     object in an external storage service.  The application layer uses
--     these fields to fetch and serve the file securely.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_attachment (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,
    ticket_message_id UUID,

    file_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size_bytes BIGINT,
    storage_provider VARCHAR(50),       -- s3|gcs|azure|local|other
    storage_key VARCHAR(500) NOT NULL,  -- object key/path
    checksum_sha256 VARCHAR(64),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_attachment_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_attachment_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_attachment_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_attachment_message
        FOREIGN KEY (ticket_message_id) REFERENCES ticket_message(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_attachment_message_tenant
        FOREIGN KEY (ticket_message_id, tenant_id) REFERENCES ticket_message(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT ck_ticket_attachment_storage_provider
        CHECK (storage_provider IS NULL OR storage_provider IN ('s3','gcs','azure','local','other'))
);

CREATE INDEX IF NOT EXISTS ix_ticket_attachment_tenant_ticket
    ON dyno_crm.ticket_attachment(tenant_id, ticket_id);

-- ----------------------------------------------------------------------
-- TICKET ASSIGNMENT HISTORY
-- ----------------------------------------------------------------------
-- Domain object: History of ticket assignments to groups/users.
-- Description:
--   This table records each assignment or reassignment of a ticket.  It
--   captures the target group and user, who made the assignment, the reason
--   for the change, and an optional reference to an AI session if the
--   assignment was produced by an AI agent (dyno_ai).  This table is
--   append-only to preserve audit history.
-- Usage in the system:
--   - UI: show assignment changes in the ticket timeline, including manual
--     and AI-driven reassignments.
--   - Reporting: analyze assignment patterns and workloads.
--   - Trigger escalation: orchestrations or automation can react when a
--     ticket moves into certain queues or to certain agents.
-- Integration:
--   - References tenant_group_shadow and tenant_user_shadow to enforce
--     tenant consistency.  AI assignments record the dyno_ai session id in
--     ai_session_id to correlate with AI automation runs.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_assignment (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,

    assigned_group_id UUID,
    assigned_user_id UUID,

    assigned_by_user_id UUID,
    assigned_by_reason VARCHAR(255),

    -- If assignment was produced by AI Workforce, store the dyno_ai session id.
    ai_session_id UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_assignment_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_assignment_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_assignment_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_assignment_group_tenant
        FOREIGN KEY (assigned_group_id, tenant_id) REFERENCES tenant_group_shadow(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_assignment_user_tenant
        FOREIGN KEY (tenant_id, assigned_user_id) REFERENCES tenant_user_shadow(tenant_id, user_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_assignment_assigned_by_user_tenant
        FOREIGN KEY (tenant_id, assigned_by_user_id) REFERENCES tenant_user_shadow(tenant_id, user_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_ticket_assignment_tenant_ticket_created
    ON dyno_crm.ticket_assignment(tenant_id, ticket_id, created_at DESC);

-- ----------------------------------------------------------------------
-- TICKET AUDIT (timeline events)
-- ----------------------------------------------------------------------
-- Domain object: Append-only audit timeline for tickets.
-- Description:
--   The ticket_audit table captures discrete events and their before/after
--   states for a ticket.  Each event records its type (status_changed,
--   priority_changed, tag_added, field_updated, message_added, etc.), who
--   caused it (contact, agent, system, or AI), and optional AI session id if
--   triggered by AI.  before/after JSONB fields store snapshots of the
--   changed properties, enabling robust audit and diffing.
-- Usage in the system:
--   - UI: timeline view for tickets showing status and priority changes,
--     tag additions, field updates, AI interactions, etc.
--   - Compliance: record immutability ensures proof of change history.
--   - Analytics: used to derive metrics (e.g. how long a ticket stayed in
--     a given status) and to feed AI training data.
-- Integration:
--   - Actor references link to contact and tenant_user_shadow for correct
--     names.  AI events link to dyno_ai sessions via ai_session_id.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_audit (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,

    event_type VARCHAR(100) NOT NULL,   -- status_changed|priority_changed|tag_added|field_updated|message_added|etc
    actor_type VARCHAR(50) NOT NULL,    -- contact|agent|system|ai

    actor_contact_id UUID,
    actor_user_id UUID,
    actor_display_name VARCHAR(255),

    -- If this audit event was produced by AI Workforce, link the dyno_ai session id.
    ai_session_id UUID,

    before JSONB,
    after JSONB,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ux_ticket_audit_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_audit_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_audit_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_audit_actor_contact
        FOREIGN KEY (actor_contact_id) REFERENCES contact(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_audit_actor_contact_tenant
        FOREIGN KEY (actor_contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_audit_actor_user_tenant
        FOREIGN KEY (tenant_id, actor_user_id) REFERENCES tenant_user_shadow(tenant_id, user_id) ON DELETE SET NULL,

    CONSTRAINT ck_ticket_audit_actor_type
        CHECK (actor_type IN ('contact','agent','system','ai'))
);

CREATE INDEX IF NOT EXISTS ix_ticket_audit_tenant_ticket_occurred
    ON dyno_crm.ticket_audit(tenant_id, ticket_id, occurred_at DESC);

-- ----------------------------------------------------------------------
-- CUSTOM FORMS / FIELDS (Zendesk-style customization)
-- ----------------------------------------------------------------------
-- Domain object: Configurable custom form definitions and values.
-- Description:
--   These tables allow tenants to define custom ticket intake forms and
--   fields.  ticket_form defines a named form that can be selected per
--   ticket.  ticket_field_def defines fields (label, type, validation).  A
--   form can include fields in an order via ticket_form_field.  Field values
--   for a ticket are stored in ticket_field_value, with one row per field.
--   This is a flexible, strongly typed alternative to the single JSONB
--   custom_fields column on ticket.
-- Usage in the system:
--   - Admin UI: create/edit forms, fields, field orders, validation rules,
--     and UI hints.  Mark forms active/inactive.
--   - Ticket creation: assign a ticket_form_id to a ticket; UI will render
--     the form and store values in ticket_field_value.
--   - Search and reporting: query ticket_field_value by field_def_id to
--     build filters and reports.
-- Integration:
--   - No external dependencies; custom forms are internal to CRM.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_form (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_ticket_form_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_form_tenant_name
    ON dyno_crm.ticket_form(tenant_id, name);

CREATE INDEX IF NOT EXISTS ix_ticket_form_tenant
    ON dyno_crm.ticket_form(tenant_id);

CREATE TABLE IF NOT EXISTS dyno_crm.ticket_field_def (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    field_key VARCHAR(100) NOT NULL,
    label VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL,      -- text|textarea|number|boolean|date|datetime|select|multiselect
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    validation JSONB,
    ui_config JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_ticket_field_def_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT ck_ticket_field_def_type
        CHECK (field_type IN ('text','textarea','number','boolean','date','datetime','select','multiselect'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_field_def_tenant_key
    ON dyno_crm.ticket_field_def(tenant_id, lower(field_key));

CREATE INDEX IF NOT EXISTS ix_ticket_field_def_tenant
    ON dyno_crm.ticket_field_def(tenant_id);

CREATE TABLE IF NOT EXISTS dyno_crm.ticket_form_field (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_form_id UUID NOT NULL,
    ticket_field_def_id UUID NOT NULL,
    display_order INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_form_field_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_form_field_form
        FOREIGN KEY (ticket_form_id) REFERENCES ticket_form(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_form_field_form_tenant
        FOREIGN KEY (ticket_form_id, tenant_id) REFERENCES ticket_form(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_form_field_field
        FOREIGN KEY (ticket_field_def_id) REFERENCES ticket_field_def(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_form_field_field_tenant
        FOREIGN KEY (ticket_field_def_id, tenant_id) REFERENCES ticket_field_def(id, tenant_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_form_field_unique
    ON dyno_crm.ticket_form_field(tenant_id, ticket_form_id, ticket_field_def_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_form_field_order
    ON dyno_crm.ticket_form_field(tenant_id, ticket_form_id, display_order);

CREATE TABLE IF NOT EXISTS dyno_crm.ticket_field_value (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,
    ticket_field_def_id UUID NOT NULL,

    value_text TEXT,
    value_number NUMERIC,
    value_bool BOOLEAN,
    value_date DATE,
    value_ts TIMESTAMPTZ,
    value_json JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_ticket_field_value_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_field_value_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_field_value_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_field_value_field
        FOREIGN KEY (ticket_field_def_id) REFERENCES ticket_field_def(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_field_value_field_tenant
        FOREIGN KEY (ticket_field_def_id, tenant_id) REFERENCES ticket_field_def(id, tenant_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_field_value_unique
    ON dyno_crm.ticket_field_value(tenant_id, ticket_id, ticket_field_def_id);

CREATE INDEX IF NOT EXISTS ix_ticket_field_value_tenant_ticket
    ON dyno_crm.ticket_field_value(tenant_id, ticket_id);

-- Add FK from ticket.ticket_form_id -> ticket_form after ticket_form exists.
ALTER TABLE dyno_crm.ticket
    ADD CONSTRAINT fk_ticket_form
    FOREIGN KEY (ticket_form_id) REFERENCES ticket_form(id) ON DELETE SET NULL;

ALTER TABLE dyno_crm.ticket
    ADD CONSTRAINT fk_ticket_form_tenant
    FOREIGN KEY (ticket_form_id, tenant_id) REFERENCES ticket_form(id, tenant_id) ON DELETE SET NULL;

-- ----------------------------------------------------------------------
-- SLA POLICY / TARGET / STATE
-- ----------------------------------------------------------------------
-- Domain objects: Service Level Agreement definitions and state.
-- Description:
--   sla_policy defines named SLA policies that can apply based on channel,
--   priority, or customer segment (encoded in match_rules).  sla_target
--   expresses per-priority thresholds for first response, next response, and
--   resolution times.  ticket_sla_state stores computed deadlines and
--   breach flags per ticket based on the policy and current status.  CRM
--   stores definitions and state; Orchestration is responsible for timer
--   evaluation and updating ticket_sla_state (e.g. via Flowable timers).
-- Usage in the system:
--   - Admin UI: create and manage SLA policies and targets.
--   - Ticket view: display deadlines and breach indicators to agents.
--   - Reporting: track compliance with SLA policies.
-- Integration:
--   - Orchestration service uses sla_policy and sla_target to schedule
--     timers, and updates ticket_sla_state via CRM API when deadlines are
--     computed or breached.
CREATE TABLE IF NOT EXISTS dyno_crm.sla_policy (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    match_rules JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_sla_policy_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_sla_policy_tenant_name
    ON dyno_crm.sla_policy(tenant_id, name);

CREATE INDEX IF NOT EXISTS ix_sla_policy_tenant
    ON dyno_crm.sla_policy(tenant_id);

CREATE TABLE IF NOT EXISTS dyno_crm.sla_target (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    sla_policy_id UUID NOT NULL,

    priority VARCHAR(50) NOT NULL,
    first_response_minutes INTEGER,
    next_response_minutes INTEGER,
    resolution_minutes INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_sla_target_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_sla_target_policy
        FOREIGN KEY (sla_policy_id) REFERENCES sla_policy(id) ON DELETE CASCADE,

    CONSTRAINT fk_sla_target_policy_tenant
        FOREIGN KEY (sla_policy_id, tenant_id) REFERENCES sla_policy(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_sla_target_priority
        CHECK (priority IN ('low','normal','high','urgent'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_sla_target_unique
    ON dyno_crm.sla_target(tenant_id, sla_policy_id, priority);

CREATE TABLE IF NOT EXISTS dyno_crm.ticket_sla_state (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,
    sla_policy_id UUID,

    first_response_due_at TIMESTAMPTZ,
    next_response_due_at TIMESTAMPTZ,
    resolution_due_at TIMESTAMPTZ,

    first_response_breached BOOLEAN NOT NULL DEFAULT FALSE,
    next_response_breached BOOLEAN NOT NULL DEFAULT FALSE,
    resolution_breached BOOLEAN NOT NULL DEFAULT FALSE,

    last_computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_ticket_sla_state_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_sla_state_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_sla_state_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_sla_state_policy
        FOREIGN KEY (sla_policy_id) REFERENCES sla_policy(id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_sla_state_policy_tenant
        FOREIGN KEY (sla_policy_id, tenant_id) REFERENCES sla_policy(id, tenant_id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_sla_state_unique
    ON dyno_crm.ticket_sla_state(tenant_id, ticket_id);

-- Now that SLA exists, connect group_profile.default_sla_policy_id safely.
ALTER TABLE dyno_crm.group_profile
    ADD CONSTRAINT fk_group_profile_default_sla_policy
    FOREIGN KEY (default_sla_policy_id) REFERENCES sla_policy(id) ON DELETE SET NULL;

ALTER TABLE dyno_crm.group_profile
    ADD CONSTRAINT fk_group_profile_default_sla_policy_tenant
    FOREIGN KEY (default_sla_policy_id, tenant_id) REFERENCES sla_policy(id, tenant_id) ON DELETE SET NULL;

-- ----------------------------------------------------------------------
-- ORCHESTRATION TASK MIRROR (Flowable -> CRM)
-- ----------------------------------------------------------------------
-- Domain object: Mirror of tasks created by the orchestration service
--   (Flowable) for a given ticket.
-- Description:
--   The ticket_task_mirror table contains a record for each task
--   representing human or system work items created in Flowable and related
--   to a ticket.  Because Flowable tasks are not persisted in CRM, this
--   mirror allows the CRM UI to display tasks and their assignments without
--   querying Flowable directly.  The orchestration_task_id is the ID of
--   the task in Flowable.  This table supports updates when tasks are
--   completed or cancelled.
-- Usage in the system:
--   - UI: display and update task status (open/completed/canceled), due date,
--     and assignment.  Show tasks in ticket detail views.
--   - Searching: filter tickets by outstanding tasks.
--   - This table is updated by listening to Flowable task events.
-- Integration:
--   - Flowable tasks: CRM listens for orchestration.task.created/updated events
--     and mirrors them here.  CRM actions (complete/claim/assign) call
--     Flowable APIs and wait for events to update this table.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_task_mirror (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,

    orchestration_task_id VARCHAR(128) NOT NULL,
    orchestration_process_instance_id VARCHAR(128),
    orchestration_process_definition_key VARCHAR(255),

    name VARCHAR(255) NOT NULL,
    description TEXT,

    status VARCHAR(50) NOT NULL DEFAULT 'open', -- open|completed|canceled
    due_at TIMESTAMPTZ,

    assigned_user_id UUID,
    assigned_group_id UUID,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ux_ticket_task_mirror_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_task_mirror_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_task_mirror_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_task_mirror_assigned_user_tenant
        FOREIGN KEY (tenant_id, assigned_user_id) REFERENCES tenant_user_shadow(tenant_id, user_id) ON DELETE SET NULL,

    CONSTRAINT fk_ticket_task_mirror_assigned_group_tenant
        FOREIGN KEY (assigned_group_id, tenant_id) REFERENCES tenant_group_shadow(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT ck_ticket_task_mirror_status
        CHECK (status IN ('open','completed','canceled'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_task_mirror_unique
    ON dyno_crm.ticket_task_mirror(tenant_id, orchestration_task_id);

CREATE INDEX IF NOT EXISTS ix_ticket_task_mirror_tenant_ticket
    ON dyno_crm.ticket_task_mirror(tenant_id, ticket_id);

CREATE INDEX IF NOT EXISTS ix_ticket_task_mirror_tenant_status
    ON dyno_crm.ticket_task_mirror(tenant_id, status);

-- ----------------------------------------------------------------------
-- AI WORKFORCE LINK (minimal pointer/history)
-- ----------------------------------------------------------------------
-- Domain object: Links tickets to AI Workforce sessions.
-- Description:
--   When a ticket is processed by an AI agent via dyno_ai, a row in
--   ticket_ai_work_ref records the session and purpose.  This allows the
--   CRM to show an AI history per ticket and to answer queries like "show
--   me tickets triaged by this agent".  It does not store full AI run logs;
--   only references to the dyno_ai work_session and summary info.
-- Usage in the system:
--   - UI: display list of AI interactions on ticket; navigate to AI details.
--   - Analytics: evaluate AI usage and outcomes across tickets.
-- Integration:
--   - dyno_ai: ai_session_id references dyno_ai.work_session.id in the AI
--     automation service.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_ai_work_ref (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,

    -- dyno_ai.work_session.id (UUID)
    ai_session_id UUID NOT NULL,

    agent_key VARCHAR(120) NOT NULL,
    purpose VARCHAR(100) NOT NULL,           -- triage|draft_reply|summarize|classify|extract|etc

    status VARCHAR(50) NOT NULL DEFAULT 'started', -- started|completed|failed|canceled
    outcome VARCHAR(50),
    confidence NUMERIC(5,4),

    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_ai_work_ref_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_ai_work_ref_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_ai_work_ref_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_ticket_ai_work_ref_status
        CHECK (status IN ('started','completed','failed','canceled')),

    CONSTRAINT ck_ticket_ai_work_ref_outcome
        CHECK (outcome IS NULL OR outcome IN ('success','partial','failed','canceled'))
);

CREATE INDEX IF NOT EXISTS ix_ticket_ai_work_ref_tenant_ticket
    ON dyno_crm.ticket_ai_work_ref(tenant_id, ticket_id, requested_at DESC);

CREATE INDEX IF NOT EXISTS ix_ticket_ai_work_ref_tenant_agent
    ON dyno_crm.ticket_ai_work_ref(tenant_id, agent_key, requested_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_ai_work_ref_unique_session
    ON dyno_crm.ticket_ai_work_ref(tenant_id, ai_session_id);

-- ----------------------------------------------------------------------
-- SUPPORT VIEWS (saved filters / queues)
-- ----------------------------------------------------------------------
-- Domain object: Saved filter/view definitions for tickets.
-- Description:
--   support_view stores saved filters, sorts, and column configurations that
--   represent "views" of tickets in the UI (e.g. "My Open Tickets", "High
--   Priority Incidents").  filter_definition is a JSON object encoding the
--   filter logic; sort_definition encodes sort preferences.  support_view
--   does not execute automation; it is purely a UI convenience.
-- Usage in the system:
--   - UI: list of views in the left sidebar; clicking a view loads the
--     filtered list.  Users with appropriate permissions can create/edit
--     views.
-- Integration:
--   - Views are local to CRM; no external dependencies.
CREATE TABLE IF NOT EXISTS dyno_crm.support_view (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    filter_definition JSONB NOT NULL,
    sort_definition JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_support_view_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_support_view_tenant_name
    ON dyno_crm.support_view(tenant_id, name);

CREATE INDEX IF NOT EXISTS ix_support_view_tenant
    ON dyno_crm.support_view(tenant_id);

-- ----------------------------------------------------------------------
-- SUPPORT MACROS (one-click agent actions)
-- ----------------------------------------------------------------------
-- Domain object: Macros for quick ticket updates.
-- Description:
--   support_macro defines pre-configured actions that agents can run with
--   one click to update a ticket.  actions is a JSON array of operations,
--   such as set_status, add_tag, assign_to_group, or add_reply.  When a
--   macro is applied to a ticket, the application layer interprets the JSON
--   and performs the updates transactionally.  These actions should
--   produce ticket_audit entries so that changes are auditable.
-- Usage in the system:
--   - UI: agents can select a macro from a list to quickly apply standard
--     responses or workflows.
--   - Admin UI: create and manage macros; enable/disable macros.
-- Integration:
--   - Macros operate within CRM; there is no external integration.  AI may
--     suggest macros but macros themselves are not AI-run.
CREATE TABLE IF NOT EXISTS dyno_crm.support_macro (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    actions JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_support_macro_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_support_macro_tenant_name
    ON dyno_crm.support_macro(tenant_id, name);

CREATE INDEX IF NOT EXISTS ix_support_macro_tenant
    ON dyno_crm.support_macro(tenant_id);

-- ----------------------------------------------------------------------
-- TIME TRACKING (optional)
-- ----------------------------------------------------------------------
-- Domain object: Time tracking entries per ticket.
-- Description:
--   ticket_time_entry records time spent by agents on tickets.  Each row
--   identifies the user who logged time, how many minutes were spent, and
--   an optional work type and note.  These entries can be used for
--   billable vs non-billable reporting, workforce management, and SLA
--   reporting.
-- Usage in the system:
--   - UI: agents can log time spent; managers can report on time spent on
--     tickets and categories of work.
-- Integration:
--   - References tenant_user_shadow for agent user id.  No external
--     integration beyond potentially exporting time tracking data to third-
--     party billing or time tracking systems via APIs.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_time_entry (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,
    user_id UUID,                        -- tenant_user_shadow.user_id
    minutes_spent INTEGER NOT NULL,
    work_type VARCHAR(50),
    note VARCHAR(500),

    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_time_entry_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_time_entry_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_time_entry_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_time_entry_user_tenant
        FOREIGN KEY (tenant_id, user_id) REFERENCES tenant_user_shadow(tenant_id, user_id) ON DELETE SET NULL,

    CONSTRAINT ck_ticket_time_entry_minutes
        CHECK (minutes_spent >= 0)
);

CREATE INDEX IF NOT EXISTS ix_ticket_time_entry_tenant_ticket
    ON dyno_crm.ticket_time_entry(tenant_id, ticket_id);

-- ----------------------------------------------------------------------
-- CSAT (optional)
-- ----------------------------------------------------------------------
-- Domain object: Customer Satisfaction surveys and responses.
-- Description:
--   csat_survey defines surveys (e.g. "How would you rate your support
--   experience?") that can be sent after a ticket is solved.  config
--   describes rating scales or question templates.  csat_response records
--   responses for tickets, capturing rating and optional comments along
--   with who responded (contact) and when.
-- Usage in the system:
--   - Admin UI: create and manage surveys; enable/disable them.
--   - After ticket solved: send survey to requester and log responses.
--   - Reporting: track satisfaction trends and agent performance.
-- Integration:
--   - Surveys may be sent via email/sms; integration with messaging services
--     is handled outside this table.  Responses are stored here.
CREATE TABLE IF NOT EXISTS dyno_crm.csat_survey (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    config JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_csat_survey_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_csat_survey_tenant_name
    ON dyno_crm.csat_survey(tenant_id, name);

CREATE TABLE IF NOT EXISTS dyno_crm.csat_response (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    csat_survey_id UUID,
    ticket_id UUID NOT NULL,
    contact_id UUID,

    rating INTEGER NOT NULL,
    comment TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_csat_response_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_csat_response_survey
        FOREIGN KEY (csat_survey_id) REFERENCES csat_survey(id) ON DELETE SET NULL,

    CONSTRAINT fk_csat_response_survey_tenant
        FOREIGN KEY (csat_survey_id, tenant_id) REFERENCES csat_survey(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT fk_csat_response_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_csat_response_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_csat_response_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE SET NULL,

    CONSTRAINT fk_csat_response_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE SET NULL,

    CONSTRAINT ck_csat_rating
        CHECK (rating >= 1 AND rating <= 5)
);

CREATE INDEX IF NOT EXISTS ix_csat_response_tenant_ticket
    ON dyno_crm.csat_response(tenant_id, ticket_id);

-- ----------------------------------------------------------------------
-- KNOWLEDGE BASE (optional, minimal but solid)
-- ----------------------------------------------------------------------
-- Domain object: Knowledge base categories, sections, articles, revisions, and feedback.
-- Description:
--   The knowledge base allows tenants to organize support content into
--   categories, sections, and articles.  Articles can have multiple
--   revisions; feedback records whether readers found them helpful.  This
--   supports self-service and agent knowledge search.
-- Usage in the system:
--   - UI: manage categories, sections, and articles; search and browse KB.
--   - Link articles from ticket replies or suggestion engines.
-- Integration:
--   - The KB is local to CRM; optionally, articles may be suggested by AI
--     based on ticket content, but storage lives here.
CREATE TABLE IF NOT EXISTS dyno_crm.kb_category (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_kb_category_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_kb_category_tenant_name
    ON dyno_crm.kb_category(tenant_id, name);

CREATE TABLE IF NOT EXISTS dyno_crm.kb_section (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    kb_category_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_kb_section_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_kb_section_category
        FOREIGN KEY (kb_category_id) REFERENCES kb_category(id) ON DELETE CASCADE,

    CONSTRAINT fk_kb_section_category_tenant
        FOREIGN KEY (kb_category_id, tenant_id) REFERENCES kb_category(id, tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_kb_section_tenant_category
    ON dyno_crm.kb_section(tenant_id, kb_category_id);

CREATE TABLE IF NOT EXISTS dyno_crm.kb_article (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    kb_section_id UUID NOT NULL,

    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255),
    is_published BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_kb_article_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_kb_article_section
        FOREIGN KEY (kb_section_id) REFERENCES kb_section(id) ON DELETE CASCADE,

    CONSTRAINT fk_kb_article_section_tenant
        FOREIGN KEY (kb_section_id, tenant_id) REFERENCES kb_section(id, tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_kb_article_tenant_section
    ON dyno_crm.kb_article(tenant_id, kb_section_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_kb_article_tenant_slug
    ON dyno_crm.kb_article(tenant_id, lower(slug))
    WHERE slug IS NOT NULL;

CREATE TABLE IF NOT EXISTS dyno_crm.kb_article_revision (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    kb_article_id UUID NOT NULL,

    version INTEGER NOT NULL,
    body TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_kb_article_revision_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_kb_article_revision_article
        FOREIGN KEY (kb_article_id) REFERENCES kb_article(id) ON DELETE CASCADE,

    CONSTRAINT fk_kb_article_revision_article_tenant
        FOREIGN KEY (kb_article_id, tenant_id) REFERENCES kb_article(id, tenant_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_kb_article_revision_unique
    ON dyno_crm.kb_article_revision(tenant_id, kb_article_id, version);

CREATE TABLE IF NOT EXISTS dyno_crm.kb_article_feedback (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    kb_article_id UUID NOT NULL,
    contact_id UUID,

    is_helpful BOOLEAN NOT NULL,
    comment TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_kb_article_feedback_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_kb_article_feedback_article
        FOREIGN KEY (kb_article_id) REFERENCES kb_article(id) ON DELETE CASCADE,

    CONSTRAINT fk_kb_article_feedback_article_tenant
        FOREIGN KEY (kb_article_id, tenant_id) REFERENCES kb_article(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_kb_article_feedback_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE SET NULL,

    CONSTRAINT fk_kb_article_feedback_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_kb_article_feedback_tenant_article
    ON dyno_crm.kb_article_feedback(tenant_id, kb_article_id);

-- ----------------------------------------------------------------------
-- REPORTING PRIMITIVES (optional)
-- ----------------------------------------------------------------------
-- Domain objects: Low-level fact tables for reporting.
-- Description:
--   ticket_metrics stores aggregate counters per ticket, such as how many
--   replies and how many times the ticket was reopened.  ticket_status_duration
--   records the durations that a ticket spends in each status, enabling
--   accurate time-in-state reporting.  These tables are typically populated
--   by background jobs or triggers reading from ticket_audit.
-- Usage in the system:
--   - Reporting UI: generate charts and reports from these fact tables.
--   - SLA analysis: correlate with ticket_sla_state.
-- Integration:
--   - Data warehousing/analytics pipelines can ingest these tables for
--     advanced analytics.
CREATE TABLE IF NOT EXISTS dyno_crm.ticket_metrics (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,

    reply_count INTEGER NOT NULL DEFAULT 0,
    reopen_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(100),

    CONSTRAINT ux_ticket_metrics_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_metrics_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_metrics_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ticket_metrics_unique
    ON dyno_crm.ticket_metrics(tenant_id, ticket_id);

CREATE TABLE IF NOT EXISTS dyno_crm.ticket_status_duration (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    ticket_id UUID NOT NULL,

    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,

    duration_seconds BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT ux_ticket_status_duration_id_tenant UNIQUE (id, tenant_id),

    CONSTRAINT fk_ticket_status_duration_ticket
        FOREIGN KEY (ticket_id) REFERENCES ticket(id) ON DELETE CASCADE,

    CONSTRAINT fk_ticket_status_duration_ticket_tenant
        FOREIGN KEY (ticket_id, tenant_id) REFERENCES ticket(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_ticket_status_duration_status
        CHECK (status IN ('new','open','pending','on_hold','solved','closed'))
);

CREATE INDEX IF NOT EXISTS ix_ticket_status_duration_tenant_ticket
    ON dyno_crm.ticket_status_duration(tenant_id, ticket_id);