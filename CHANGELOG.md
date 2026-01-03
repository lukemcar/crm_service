## [2026-01-02] – Test Suite Update and Final Review

### Added
* Introduced a dedicated continuation phase to review and validate the refactored codebase prior to final packaging.  Verified that all newly added route modules, service functions and message producers compile without syntax errors and that imports resolve correctly.  Used `python -m compileall` to ensure there were no outstanding syntax issues across the codebase.
* Added comprehensive test coverage for the refactored domains.  New test modules (`test_list_routes.py`, `test_list_membership_routes.py`, `test_pipeline_routes.py`, `test_pipeline_stage_routes.py`) were created to exercise the new admin and tenant endpoints, nested resource patterns, pagination and audit header propagation.  Existing tests for activities, associations and deals were adjusted to call the new service functions and verify audit fields.

### Changed
* Updated the existing test suite under `tests/` to replace references to legacy routes for the Activity, Association and Deal domains with calls to the new admin and tenant endpoints.  Adjusted assertions to verify that audit information from the `X‑User` header is passed through to the service layer.
* Ensured that new tests supply `limit` and `offset` query parameters where appropriate and validate that filters and pagination are forwarded correctly to the service layer.

### Notes
* This final review ensures that the refactored codebase is syntactically sound and ready for packaging.  All domain refactors have been completed and the application compiles successfully.  A test suite covering the refactored domains has been added and compiles successfully.  The next step is to archive the final codebase into a zip file for delivery.

## [2026-01-02] – Activity Domain Refactor

### Added
* Added admin and tenant route modules (`activities_admin_route.py` and `activities_tenant_route.py`) to replace the old `activity.py` route. Admin routes live under `/admin/activities` and tenant routes under `/tenants/{tenant_id}/activities`. Each route delegates to the service layer and uses the `X-User` header for audit fields.

### Changed
* Refactored the activity service (`activity_service.py`) to use `commit_or_raise`, compute snapshots and changes, and emit events after committing transactions using the new `ActivityMessageProducer`.
* Replaced `ActivityProducer` with `ActivityMessageProducer` following the canonical messaging pattern. Task names now derive from the global `EXCHANGE_NAME` and include message headers with the tenant ID.
* Updated `main_api.py` and route aggregator to include the new routers and remove the legacy activity router.
* Updated event model imports and service usage accordingly.

### Notes
* The original `app/api/routes/activity.py` remains for backward compatibility but is no longer included in the FastAPI application.

## [2026-01-02] – Association Domain Refactor

### Added
* Added admin and tenant route modules (`associations_admin_route.py` and `associations_tenant_route.py`) to replace the old `association.py` route.  Admin routes live under `/admin/associations` and tenant routes under `/tenants/{tenant_id}/associations`.  Each route delegates to the service layer and uses the `X-User` header for audit fields.

### Changed
* Refactored the association service (`association_service.py`) to use `commit_or_raise`, compute snapshots for created events, and emit events after committing transactions using the new `AssociationMessageProducer`.
* Replaced `AssociationProducer` with `AssociationMessageProducer` following the canonical messaging pattern.  Task names now derive from the global `EXCHANGE_NAME` and include message headers with the tenant ID.
* Updated `main_api.py` and the route aggregator to include the new routers and remove the legacy association router.
* Updated producer exports and service imports accordingly.

### Notes
* Associations are immutable; therefore only created and deleted events are emitted.  The original `app/api/routes/association.py` remains for backward compatibility but is no longer included in the FastAPI application.

## [2026-01-02] – Deal Domain Refactor

### Added
* Added admin and tenant route modules (`deals_admin_route.py` and `deals_tenant_route.py`) to replace the old `deal.py` route.  Admin routes live under `/admin/deals` and support cross‑tenant listing with optional pipeline and stage filters.  Tenant routes live under `/tenants/{tenant_id}/deals` and scope operations to a single tenant.  Mutations use the `X-User` header to populate audit fields.

### Changed
* Refactored the deal service (`deal_service.py`) to use `commit_or_raise`, compute snapshots and changes, and emit events after committing transactions via the new `DealMessageProducer`.
* Replaced `DealProducer` with `DealMessageProducer` following the canonical messaging pattern.  Task names now derive from the global `EXCHANGE_NAME` and include message headers with the tenant ID.  A `DealProducer` alias is retained for backward compatibility.
* Updated the route aggregator and `main_api.py` to include the new deals routers and remove the legacy `deal` router.
* Updated producer exports and service imports accordingly.

### Notes
* The original `app/api/routes/deal.py` remains in the codebase for backward compatibility but is no longer included in the FastAPI application.

## [2026-01-02] – List Domain Refactor

### Added
* Added admin and tenant route modules (`lists_admin_route.py` and `lists_tenant_route.py`) to replace the old `list.py` route.  Admin routes live under `/admin/lists` and support cross‑tenant listing with optional filters and pagination.  Tenant routes live under `/tenants/{tenant_id}/lists` and scope operations to a single tenant.  Mutations use the `X‑User` header to populate audit fields.

### Changed
* Refactored the list service (`list_service.py`) to use `commit_or_raise`, compute snapshots and change sets, and emit events after committing transactions via the new `ListMessageProducer`.  Added helper functions for listing, retrieving, creating, updating and deleting lists under the `service_*` namespace.
* Replaced `ListProducer` with `ListMessageProducer` following the canonical messaging pattern.  Task names now derive from the global `EXCHANGE_NAME` and include message headers with the tenant ID.  A `ListProducer` alias is retained for backward compatibility.
* Updated the route aggregator (`app/api/routes/__init__.py`) and `main_api.py` to include the new list routers and removed the legacy `list_router` from the application.  Legacy `list.py` remains in the codebase for backwards compatibility but is no longer used.

### Notes
* List event payloads now include the list ID, name, object type, list type, filter definition and audit fields.  The `changes` dictionary for update events contains only the fields that have been modified.  The old list routes remain accessible for transitional purposes but will be removed in a future release.

## [2026-01-02] – List Membership Domain Refactor

### Added
* Added admin and tenant route modules (`list_memberships_admin_route.py` and `list_memberships_tenant_route.py`) to replace the old `list_membership.py` route.  Collection endpoints are nested under lists (`/admin/lists/{list_id}/memberships` and `/tenants/{tenant_id}/lists/{list_id}/memberships`) while singleton endpoints use flat paths (`/admin/memberships/{membership_id}` and `/tenants/{tenant_id}/memberships/{membership_id}`).  Mutations accept the `X‑User` header for audit fields.

### Changed
* Refactored the list membership service (`list_membership_service.py`) to use `commit_or_raise`, compute snapshots and emit events via the new `ListMembershipMessageProducer`.  Added helper functions `service_list_memberships`, `service_get_membership`, `service_create_membership` and `service_delete_membership` to encapsulate business logic and event emission.
* Replaced `ListMembershipProducer` with `ListMembershipMessageProducer` following the canonical messaging pattern.  Task names now derive from the global `EXCHANGE_NAME` and include message headers with the tenant ID.  A `ListMembershipProducer` alias is retained for backward compatibility.
* Updated the route aggregator and `main_api.py` to include the new list membership routers and removed the legacy `list_membership_router` from the application.

### Notes
* List membership event payloads now include the membership ID, list ID, member ID, member type and audit fields.  The original `list_membership.py` remains in the codebase for backwards compatibility but is no longer included in the FastAPI application.

## [2026-01-02] – Pipeline Domain Refactor

### Added
* Added admin and tenant route modules (`pipelines_admin_route.py` and `pipelines_tenant_route.py`) to replace the old `pipeline.py` route.  Admin routes live under `/admin/pipelines` and support cross‑tenant listing with optional name filters and pagination.  Tenant routes live under `/tenants/{tenant_id}/pipelines` and scope operations to a single tenant.  Mutating operations use the `X‑User` header to populate audit fields.

### Changed
* Refactored the pipeline service (`pipeline_service.py`) to provide new helper functions `service_list_pipelines`, `service_get_pipeline`, `service_create_pipeline`, `service_update_pipeline` and `service_delete_pipeline`.  These functions use `commit_or_raise`, compute snapshots and change sets, and emit events via the new `PipelineMessageProducer` after committing.  Existing functions remain for backwards compatibility.
* Replaced `PipelineProducer` with `PipelineMessageProducer` following the canonical messaging pattern.  Task names now derive from the global `EXCHANGE_NAME` and include message headers with the tenant ID.  A `PipelineProducer` alias is retained for backward compatibility.
* Updated the route aggregator and `main_api.py` to include the new pipeline routers and removed the legacy `pipeline_router` from the application.

### Notes
* Pipeline event payloads now include the pipeline ID, name and audit fields.  Update events emit only the changed fields.  The old `pipeline.py` remains for backwards compatibility but is no longer used.

## [2026-01-02] – Pipeline Stage Domain Refactor

### Added
* Added admin and tenant route modules (`pipeline_stages_admin_route.py` and `pipeline_stages_tenant_route.py`) to replace the old `pipeline_stage.py` route.  Collection endpoints are nested under pipelines (`/admin/pipelines/{pipeline_id}/stages` and `/tenants/{tenant_id}/pipelines/{pipeline_id}/stages`) while singleton endpoints use flat paths (`/admin/stages/{stage_id}` and `/tenants/{tenant_id}/stages/{stage_id}`).  Mutations accept the `X‑User` header for audit fields.

### Changed
* Refactored the pipeline stage service (`pipeline_stage_service.py`) to use `commit_or_raise`, validate pipeline existence and ownership, detect duplicate stage names and orders, compute snapshots and change sets, and emit events via the new `PipelineStageMessageProducer`.  Added helper functions `service_list_stages`, `service_get_stage`, `service_create_stage`, `service_update_stage` and `service_delete_stage` to encapsulate this logic.  Legacy functions remain for backward compatibility.
* Replaced `PipelineStageProducer` with `PipelineStageMessageProducer` following the canonical messaging pattern.  Task names now derive from the global `EXCHANGE_NAME` and include message headers with the tenant ID.  A `PipelineStageProducer` alias is retained for backward compatibility.
* Updated the route aggregator and `main_api.py` to include the new pipeline stage routers and removed the legacy `pipeline_stage_router` from the application.

### Notes
* Pipeline stage event payloads now include the stage ID, pipeline ID, name, order, probability and audit fields.  Update events emit only changed fields.  The original `pipeline_stage.py` remains in the codebase for backward compatibility but is no longer used.

## [2026-01-01] – Reserved Attribute Fix (metadata)

### Changed
* Renamed ORM attributes from `metadata` → `provider_metadata` on the `TicketMessage` model (the database column remains `"metadata"`).
* Updated Pydantic schemas (`TicketMessageBase`, `TenantCreateTicketMessage`, `AdminCreateTicketMessage`, and `TicketMessageOut`) to use `provider_metadata` instead of `metadata`.
* Updated service layer and event payloads to reference `provider_metadata` and propagate the renamed field.

### Tests
* Updated ticket message nested routes tests to construct and validate message objects using the `provider_metadata` field.

### Notes
* The term `metadata` is reserved by SQLAlchemy’s Declarative API for table metadata.  Using `metadata` as an attribute on a model class results in an import‑time error.  Renaming the attribute to `provider_metadata` avoids this conflict while keeping the database column name unchanged.

## [2026-01-01] – Fix SQLAlchemy Postgres Index Sort Order Declarations

### Changed
* Replaced unsupported `postgresql_sort_order` kwarg in `app/domain/models/ticket_message.py` index declaration with a descending `created_at` clause using `text("created_at DESC")`.
* All models now import without raising an `ArgumentError` for unsupported index arguments.

### Tests
* Added `tests/test_models_import.py` to ensure all models import cleanly and index definitions compile.

### Notes
* When specifying sorted indexes in SQLAlchemy, provide ordering in the index column expression rather than via unsupported keyword arguments.  See SQLAlchemy documentation for details.

## [2026-01-01] – Support Domain Implementation (reporting primitives)

### Added
* Added **ticket metrics** and **ticket status duration** domains to support reporting and analytics.  Introduced SQLAlchemy models (`TicketMetrics`, `TicketStatusDuration`) with tenant‑scoped foreign keys to tickets and unique constraints enforcing one record per ticket.  Metrics store counts of replies and reopen events, while status duration records capture intervals that a ticket spent in each status.
* Implemented Pydantic schemas for metrics (`TicketMetricsBase`, `AdminCreateTicketMetrics`, `TicketMetricsUpdate`, `TicketMetricsOut`) and status durations (`TicketStatusDurationBase`, `AdminCreateTicketStatusDuration`, `AdminUpdateTicketStatusDuration`, `TicketStatusDurationOut`) to validate request and response bodies.
* Added event schemas (`TicketMetricsCreatedEvent`, `TicketMetricsUpdatedEvent`, `TicketMetricsDeletedEvent`, `TicketStatusDurationCreatedEvent`, `TicketStatusDurationUpdatedEvent`, `TicketStatusDurationDeletedEvent`) and message producers (`TicketMetricsMessageProducer`, `TicketStatusDurationMessageProducer`) that publish lifecycle events to the messaging layer.
* Developed service layers (`ticket_metrics_service.py`, `ticket_status_duration_service.py`) providing list, create, get, update and delete operations with tenant scoping, snapshot/delta computation, and event emission on mutations.  Listing functions support optional filtering and pagination.
* Added nested tenant endpoints under `/tenants/{tenant_id}/tickets/{ticket_id}` for listing and retrieving metrics and status durations (`/metrics`, `/metrics/{metrics_id}`, `/status_durations`, `/status_durations/{duration_id}`).  These endpoints are read‑only for tenants.
* Added nested admin endpoints under `/admin/tickets/{ticket_id}` for listing, creating, updating and deleting metrics and status durations with explicit tenant scoping via query parameters.  Admin endpoints accept request bodies conforming to the Pydantic schemas and populate audit fields from the `X-User` header.
* Added comprehensive tests (`test_ticket_reporting_nested_routes.py`, `test_ticket_reporting_admin_nested_routes.py`) verifying that route handlers delegate correctly to the service layer, propagate tenant and ticket identifiers, and use the `X‑User` header for audit in admin contexts.  Extended `test_producers.py` to ensure the new producers publish events with the correct task names and headers.

### Changed
* Updated router modules (`tickets_tenant_nested_routes.py` and `tickets_admin_nested_routes.py`) to include metrics and status duration endpoints and import the new services and schemas.
* Updated exports in `app/domain/models/__init__.py`, `app/domain/schemas/__init__.py`, and `app/messaging/producers/__init__.py` to include the new reporting primitives.

### Notes
* Reporting primitives are populated by background jobs that read audit logs and message events.  Tenants can view but not modify these records.  Admin APIs allow creation and updates for backfilling or manual corrections.  The remaining support domain tasks include final code review and completeness verification.

## [2026-01-01] – Support Domain Implementation (knowledge base)

### Added
* Implemented the **knowledge base** domain, enabling tenants and admins to manage support articles and related content.  Added SQLAlchemy models for categories (`KbCategory`), sections (`KbSection`), articles (`KbArticle`), article revisions (`KbArticleRevision`), and article feedback (`KbArticleFeedback`) with tenant‑scoped foreign keys, uniqueness constraints, slug normalization for articles, and audit fields.
* Added Pydantic schemas for each domain object (base, tenant/admin create, update, and output models) to validate request and response bodies and to enforce immutability of certain fields such as slugs.  Schemas reside in the `app/domain/schemas` package and are exported for use in routes and services.
* Created event schemas and message producers for knowledge base categories, sections, articles, revisions and feedback.  Events follow the `<exchange>.kb_<object>.<action>` naming convention and include delta payloads for updates.  Producers (`KbCategoryMessageProducer`, `KbSectionMessageProducer`, `KbArticleMessageProducer`, `KbArticleRevisionMessageProducer`, `KbArticleFeedbackMessageProducer`) encapsulate event publishing logic.
* Developed service layers for categories, sections, articles, revisions and feedback.  Services provide list, create, get, update (where applicable) and delete operations with tenant scoping, snapshot/delta computation, slug normalization for articles, and event emission.  Revisions and feedback are append‑only and do not support updates.
* Added tenant‑scoped and admin‑scoped API routes for categories, sections, articles, revisions and feedback.  Routes follow the pattern `/tenants/{tenant_id}/kb_*` for tenants and `/admin/kb_*` with `tenant_id` query parameter for admins.  Nested routes allow creating and listing revisions and feedback under articles.  Audit fields are populated from the `X‑User` header where applicable.  Fixed Python syntax errors in tenant routes by ensuring request body parameters appear before default path parameters.
* Added knowledge base models, schemas and producers to the respective `__init__.py` exports and wired the new routers into the application via `api/routes/__init__.py` and `main_api.py`.

### Changed
* Reordered function parameters in tenant knowledge base route modules (`kb_articles_tenant_route.py`, `kb_sections_tenant_route.py`, `kb_article_revisions_tenant_route.py`, `kb_article_feedback_tenant_route.py`) to ensure non‑default request body parameters precede default path parameters.  This resolves `SyntaxError: non-default argument follows default argument` during compilation.
* Updated `app/domain/models/__init__.py`, `app/domain/schemas/__init__.py`, and `app/messaging/producers/__init__.py` to include the knowledge base components.

### Notes
* Knowledge base entities support full CRUD operations except for article revisions and feedback, which are append‑only.  Slugs on articles are normalized to lower case for uniqueness.  Test suites for the knowledge base domain will be added in a future iteration to verify service delegation and producer behavior.

## [2026-01-01] – Support Domain Implementation (task mirrors & AI work refs)

### Added
* Implemented **ticket task mirror** domain to mirror tasks from the orchestration service. Added SQLAlchemy model (`TicketTaskMirror`) with tenant and ticket foreign keys, task identifiers, metadata, status, due date and assignment fields, plus audit timestamps.  Added Pydantic schemas (`TicketTaskMirrorBase`, `AdminUpsertTicketTaskMirror`, `TicketTaskMirrorOut`) to validate request and response bodies.
* Added event schemas (`TicketTaskMirrorCreatedEvent`, `TicketTaskMirrorUpdatedEvent`, `TicketTaskMirrorDeletedEvent`) and message producer (`TicketTaskMirrorMessageProducer`) to publish task mirror lifecycle events. Added service layer (`ticket_task_mirror_service.py`) providing list, get, upsert and delete operations with snapshot/delta computation and event emission.
* Added **read‑only tenant endpoints** to list and retrieve task mirrors under `/tenants/{tenant_id}/tickets/{ticket_id}/task_mirrors` and to retrieve a single task mirror by ID.  Added **admin nested endpoints** to list and retrieve task mirrors with explicit tenant scoping.  Added **admin top‑level endpoints** (`/admin/ticket_task_mirrors`) to upsert and delete task mirrors across tenants.  Updated router aggregation and `main_api.py` wiring to include these routes.

* Implemented **ticket AI work reference** domain linking tickets to AI Workforce sessions. Added SQLAlchemy model (`TicketAiWorkRef`) capturing the session ID, agent key, purpose, status, outcome, confidence and timestamps.  Added Pydantic schemas (`TicketAiWorkRefBase`, `AdminUpsertTicketAiWorkRef`, `TicketAiWorkRefOut`).
* Added event schemas (`TicketAiWorkRefCreatedEvent`, `TicketAiWorkRefUpdatedEvent`, `TicketAiWorkRefDeletedEvent`) and message producer (`TicketAiWorkRefMessageProducer`) to publish AI work reference lifecycle events. Added service layer (`ticket_ai_work_ref_service.py`) providing list, get, upsert and delete operations with snapshot/delta computation and event emission.
* Added **read‑only tenant endpoints** to list and retrieve AI work references under `/tenants/{tenant_id}/tickets/{ticket_id}/ai_work_refs`.  Added **admin nested endpoints** to list and retrieve references with tenant scoping.  Added **admin top‑level endpoints** (`/admin/ticket_ai_work_refs`) to upsert and delete AI work references across tenants.  Updated router aggregation and `main_api.py` wiring accordingly.
* Added tests for the new nested and admin endpoints in `tests/test_ticket_task_ai_nested_routes.py` and `tests/test_ticket_task_ai_admin_routes.py` verifying that route handlers delegate correctly to the service layer and propagate parameters and audit headers.  Extended `tests/test_producers.py` to cover the new producers.

### Changed
* Updated `app/domain/models/__init__.py`, `app/domain/schemas/__init__.py`, and `app/messaging/producers/__init__.py` to expose the new models, schemas and producers.
* Added new admin route modules (`ticket_task_mirrors_admin_route.py`, `ticket_ai_work_refs_admin_route.py`) and updated route aggregator and application wiring to include them.

### Notes
* Task mirrors and AI work references are read‑only for tenants; only admin/internal APIs can create or update them.  These features improve visibility of orchestration tasks and AI sessions in the CRM UI.
* Remaining support domain features include time tracking/CSAT, knowledge base, reporting primitives and a final code review. These will be implemented in subsequent iterations.

## [2026-01-01] – Support Domain Implementation (support views & macros)

### Added
* Introduced support view domain, allowing tenants and admins to define saved ticket list views.  Added SQLAlchemy model (`SupportView`) with fields for name, description, active status, `filter_definition` and `sort_definition`, and tenant scoping with audit fields.
* Implemented Pydantic schemas for views: `SupportViewBase`, `TenantCreateSupportView`, `AdminCreateSupportView`, `SupportViewUpdate`, and `SupportViewOut` to validate request and response bodies.
* Added event schemas (`SupportViewCreatedEvent`, `SupportViewUpdatedEvent`, `SupportViewDeletedEvent`) and message producer (`SupportViewMessageProducer`) that publishes lifecycle events to the messaging layer.
* Developed a service layer (`support_view_service.py`) providing list, create, get, update and delete operations with tenant scoping, snapshot and delta computation, audit field handling, and event emission on mutations.
* Added tenant‑scoped and admin‑scoped API routes for support views under `/tenants/{tenant_id}/support_views` and `/admin/support_views`.  Endpoints support listing with filters on `is_active`, pagination, creation, partial updates via PATCH, retrieval and deletion.
* Created tests in `tests/test_support_views.py` verifying that tenant route handlers delegate correctly to the service layer, propagate the `X‑User` header for audit fields, and pass filter parameters.  Extended `tests/test_producers.py` to cover the new support view producer.

* Introduced support macro domain, enabling definition of macros composed of a list of actions to perform on tickets.  Added SQLAlchemy model (`SupportMacro`) with fields for name, description, active status, and an `actions` JSON array, along with tenant scoping and audit fields.
* Implemented Pydantic schemas for macros: `SupportMacroBase`, `TenantCreateSupportMacro`, `AdminCreateSupportMacro`, `SupportMacroUpdate`, and `SupportMacroOut`.
* Added event schemas (`SupportMacroCreatedEvent`, `SupportMacroUpdatedEvent`, `SupportMacroDeletedEvent`) and message producer (`SupportMacroMessageProducer`) for publishing macro lifecycle events.
* Developed a service layer (`support_macro_service.py`) providing list, create, get, update and delete operations with tenant scoping, snapshot/delta computation and event emission.
* Added tenant‑scoped and admin‑scoped API routes for support macros under `/tenants/{tenant_id}/support_macros` and `/admin/support_macros`.  Routes support listing with filters on `is_active`, creation, partial updates, retrieval and deletion.
* Added tests in `tests/test_support_macros.py` verifying that tenant route handlers delegate correctly to the service layer and propagate the `X‑User` header.  Extended `tests/test_producers.py` to ensure the support macro producer publishes events with the correct task names and headers.

### Changed
* Updated router aggregation (`api/routes/__init__.py`) and `main_api.py` wiring to include the new support view and macro routes.
* Updated exports in `app/domain/models/__init__.py`, `app/domain/schemas/__init__.py`, and `app/messaging/producers/__init__.py` to include the support view and macro models, schemas and producers.

### Notes
* Support views and macros support full CRUD operations.  Macros contain JSON arrays of operations that the application layer interprets during execution.  Further support domain features (time tracking/CSAT, knowledge base, reporting primitives and AI pointers) remain to be implemented.

## [2025-12-31] – Support Domain Implementation (ticket messages)

### Added
* Implemented ticket message nested resource: added SQLAlchemy model (`TicketMessage`) previously introduced but now exposed via Pydantic schemas (`TicketMessageBase`, `TenantCreateTicketMessage`, `AdminCreateTicketMessage`, `TicketMessageOut`).
* Added event schemas (`TicketMessageCreatedEvent`) and message producer (`TicketMessageMessageProducer`) for publishing message creation events.
* Developed service layer (`ticket_message_service.py`) providing list and create operations with tenant scoping, snapshot generation, and event emission.
* Added tenant‑scoped and admin‑scoped nested API routes for messages under `/tenants/{tenant_id}/tickets/{ticket_id}/messages` and `/admin/tickets/{ticket_id}/messages`, supporting list and create operations with optional filters on author_type, is_public, and channel_type.
* Added tests in `tests/test_ticket_message_nested_routes.py` verifying that nested message route handlers delegate correctly to the service layer and propagate the `X‑User` header. Extended `tests/test_producers.py` to cover the new ticket message producer.

### Changed
* Updated router modules (`tickets_tenant_nested_routes.py` and `tickets_admin_nested_routes.py`) to include message endpoints and import the new service and schemas.
* Updated exports in `app/domain/models/__init__.py`, `app/domain/schemas/__init__.py`, and `app/messaging/producers/__init__.py` to include `TicketMessage`, its schemas, and the new producer.

### Notes
* Messages are append-only; update and delete operations are not supported. Further nested ticket resources (attachments, assignments, audits) remain to be implemented.

## [2026-01-01] – Support Domain Implementation (ticket forms)

### Added
* Introduced a new domain for custom ticket forms. Added SQLAlchemy model (`TicketForm`) representing form definitions with fields for name, description, active status and audit metadata.
* Implemented Pydantic schemas for requests and responses: `TicketFormBase`, `TenantCreateTicketForm`, `AdminCreateTicketForm`, `TicketFormUpdate`, and `TicketFormOut` to mirror the ORM model and support validation.
* Added event schemas (`TicketFormCreatedEvent`, `TicketFormUpdatedEvent`, `TicketFormDeletedEvent`) and a message producer (`TicketFormMessageProducer`) that publishes lifecycle events to the messaging layer.
* Developed a service layer (`ticket_form_service.py`) providing CRUD operations with tenant scoping, snapshot and delta computation, audit field handling, and event emission on mutations.
* Added tenant‑scoped and admin‑scoped API routes for ticket forms under `/tenants/{tenant_id}/ticket_forms` and `/admin/ticket_forms`. These endpoints support listing with pagination and active status filtering, creation, partial updates via PATCH, retrieval and deletion. Audit fields are populated from the `X-User` header.
* Added tests in `tests/test_ticket_form_routes.py` verifying that tenant route handlers delegate correctly to the service layer, propagate the `X‑User` header, and pass filter parameters. Added tests in `tests/test_producers.py` to ensure the ticket form producer publishes events with correct task names and headers.

### Changed
* Updated router aggregation (`api/routes/__init__.py`) and `main_api.py` to include the new ticket form routes.
* Updated exports in `app/domain/models/__init__.py`, `app/domain/schemas/__init__.py`, and `app/messaging/producers/__init__.py` to include ticket form components.

### Notes
* Custom forms are managed at the tenant or admin level. Field definitions and values will be implemented in subsequent iterations of the support domain.

## [2025-12-31] – Support Domain Implementation (ticket attachments)

### Added
* Added support for ticket attachments as a nested resource under tickets.  Defined SQLAlchemy model (`TicketAttachment`) and Pydantic schemas (`TicketAttachmentBase`, `TenantCreateTicketAttachment`, `AdminCreateTicketAttachment`, `TicketAttachmentOut`).
* Implemented event schemas (`TicketAttachmentCreatedEvent`, `TicketAttachmentDeletedEvent`) and message producer (`TicketAttachmentMessageProducer`) for publishing attachment creation and deletion events.
* Developed service layer (`ticket_attachment_service.py`) providing list, create, get and delete operations with tenant scoping, snapshot generation and event emission.
* Added tenant‑scoped and admin‑scoped nested API routes for attachments under `/tenants/{tenant_id}/tickets/{ticket_id}/attachments` and `/admin/tickets/{ticket_id}/attachments`, supporting list, create and delete operations with optional filters for `ticket_message_id` and `storage_provider`.
* Added tests in `tests/test_ticket_attachment_nested_routes.py` verifying that nested attachment route handlers delegate correctly to the service layer, propagate the `X‑User` header, and pass filter parameters. Extended `tests/test_producers.py` to cover the new ticket attachment producer.

### Changed
* Updated router modules (`tickets_tenant_nested_routes.py` and `tickets_admin_nested_routes.py`) to include attachment endpoints and import the new service and schemas.
* Updated exports in `app/domain/schemas/__init__.py` and `app/messaging/producers/__init__.py` to include ticket attachment schemas and producer.

### Notes
* Attachments are append-only; update operations are not supported. Further nested resources (assignments, audits) and other support domain features remain to be implemented in future iterations.

## [2025-12-31] – Support Domain Implementation (ticket assignments and audits)

### Added
* Added support for ticket assignment history as a nested resource under tickets.  Introduced SQLAlchemy model (`TicketAssignment`) and Pydantic schemas (`TicketAssignmentBase`, `TenantCreateTicketAssignment`, `AdminCreateTicketAssignment`, `TicketAssignmentOut`).
* Implemented event schema (`TicketAssignmentCreatedEvent`) and message producer (`TicketAssignmentMessageProducer`) for publishing assignment creation events.
* Developed service layer (`ticket_assignment_service.py`) providing list and create operations with tenant scoping, snapshot generation, and event emission.
* Added tenant‑scoped and admin‑scoped nested API routes for assignments under `/tenants/{tenant_id}/tickets/{ticket_id}/assignments` and `/admin/tickets/{ticket_id}/assignments`, supporting list and create operations.
* Introduced ticket audit read‑only resource: added SQLAlchemy model (`TicketAudit`), response schema (`TicketAuditOut`), optional event schema (`TicketAuditCreatedEvent`) and producer (`TicketAuditMessageProducer`), service layer (`ticket_audit_service.py`) with list and create (internal) operations, and tenant/admin nested routes to list audit events under `/audits`.
* Added tests in `tests/test_ticket_assignment_audit_nested_routes.py` verifying that assignment and audit route handlers delegate correctly to the service layer, propagate the `X‑User` header for assignments, and pass filter parameters. Extended `tests/test_producers.py` to cover the new assignment and audit producers.

### Changed
* Updated router modules (`tickets_tenant_nested_routes.py` and `tickets_admin_nested_routes.py`) to include assignment and audit endpoints and import the new services and schemas.
* Updated exports in `app/domain/models/__init__.py`, `app/domain/schemas/__init__.py`, and `app/messaging/producers/__init__.py` to include ticket assignment and audit models, schemas, and producers.
* Included ticket assignment and audit events in the event schemas package.

### Notes
* Assignments and audits are append-only. Update and delete operations are not supported. Additional support domain features (custom forms/fields, SLA management, orchestration/AI integration, views & macros, time tracking & CSAT, knowledge base, and reporting primitives) remain to be implemented.

## [2025-12-31] – Support Domain Implementation (ticket participants and tags)

### Added
* Introduced nested resources for tickets: participants and tags. Added SQLAlchemy models (`TicketParticipant` and `TicketTag`) with composite foreign keys and appropriate uniqueness and check constraints.
* Implemented Pydantic request/response schemas (`TicketParticipantBase`, `TenantCreateTicketParticipant`, `AdminCreateTicketParticipant`, `TicketParticipantOut`, `TicketTagBase`, `TenantCreateTicketTag`, `AdminCreateTicketTag`, `TicketTagOut`).
* Added event schemas (`TicketParticipantCreatedEvent`, `TicketParticipantDeletedEvent`, `TicketTagCreatedEvent`, `TicketTagDeletedEvent`) and corresponding message producers (`TicketParticipantMessageProducer`, `TicketTagMessageProducer`).
* Developed service layers (`ticket_participant_service.py`, `ticket_tag_service.py`) with list, create, and delete operations, including snapshot generation and event emission.
* Created tenant‑scoped nested API routes under `/tenants/{tenant_id}/tickets/{ticket_id}` for participants and tags, supporting list, create, and delete operations. Added admin‑scoped nested routes under `/admin/tickets/{ticket_id}` with explicit tenant_id query parameters.
* Added tests in `tests/test_ticket_nested_routes.py` verifying that nested route handlers delegate correctly to the respective service layer and propagate the `X‑User` header. Extended `tests/test_producers.py` to cover the new ticket participant and tag producers.

### Changed
* Updated router aggregation (`api/routes/__init__.py`) and `main_api.py` wiring to include new nested routes.
* Added exports for the new models, schemas, and producers in their respective `__init__.py` modules.

### Notes
* Participants and tags are append‑only and thus only support create and delete operations. Update functionality is intentionally omitted. Further nested resources (messages, attachments, assignments, audits) remain to be implemented in future iterations.

## [2025-12-31] – Support Domain Implementation (tickets)

### Added
* Introduced the ticket core domain including full CRUD support for support cases. Added SQLAlchemy model (`Ticket`), Pydantic request and response schemas (`TicketBase`, `TenantCreateTicket`, `AdminCreateTicket`, `TicketUpdate`, `TicketOut`), event schemas for ticket creation, update and deletion, and a message producer (`TicketMessageProducer`) emitting events on mutations.
* Implemented service layer functions in `ticket_service.py` providing list, create, get, update and delete operations with audit fields and delta computation for update events. Services publish the appropriate ticket events after successful database commits.
* Added tenant‑scoped and admin‑scoped API routes for tickets under `/tenants/{tenant_id}/tickets` and `/admin/tickets`, supporting listing with filters (status, priority, assignee), creation, partial updates via PATCH, retrieval and deletion.

### Changed
* Updated router aggregation (`api/routes/__init__.py`) and `main_api.py` wiring to include the new ticket routes.
* Updated exports in `app/domain/schemas/__init__.py` to expose ticket schemas and `app/messaging/producers/__init__.py` to expose `TicketMessageProducer`.
* Added tests `tests/test_ticket_routes.py` verifying that the ticket route handlers delegate correctly to the service layer and propagate the `X-User` header for audit fields. Extended `tests/test_producers.py` to cover `TicketMessageProducer`.

### Notes
* Nested ticket resources (participants, tags, messages, attachments, assignments, audits) as well as additional support domains will be implemented in subsequent iterations.

## [2025-12-31] – Support Domain Implementation (continued)

### Added
- Implemented group profile domain (support queue metadata) including SQLAlchemy model
  (`GroupProfile`), Pydantic schemas (create/update/out), event schemas,
  message producer, and service layer functions.  This lays the
  groundwork for managing support queue settings such as SLA defaults
  and AI posture.
- Added tenant and admin API routes for group profiles at
  `/tenants/{tenant_id}/group_profiles` and `/admin/group_profiles`.
  These endpoints support list, create, update, retrieve and delete
  operations.  Routing registration and endpoint functions follow
  existing patterns (DTO → service → DTO).
- Implemented inbound channel domain to describe entry points for
  support tickets.  Added ORM model (`InboundChannel`), request and
  response schemas (`TenantCreateInboundChannel`, `AdminCreateInboundChannel`,
  `InboundChannelUpdate`, `InboundChannelOut`), event models and
  producer, service layer functions, and both tenant‑scoped and
  admin‑scoped API routes under `/tenants/{tenant_id}/inbound_channels`
  and `/admin/inbound_channels`.

### Changed
- Updated router aggregation and `main_api.py` wiring to include
  group profile and inbound channel routes.
- Updated model and schema exports in the respective `__init__.py`
  modules to include the new domain types.  Extended the messaging
  producer exports to expose the new producers.

### Tests
- Added preliminary tests in `tests/test_producers.py` verifying
  task naming and payload construction for the inbound channel and
  group profile message producers.
- Added `tests/test_inbound_channel.py` to ensure tenant and admin
  route functions delegate correctly to the service layer and honour
  the `X-User` header for audit fields.

### Notes
- Group profile routes and end‑to‑end tests will be implemented in
  subsequent iterations.  Uniqueness and enumeration constraints are
  enforced at the database layer; service functions rely on
  `commit_or_raise` to surface any integrity errors.

## [2025-12-31] – Support Domain Implementation

### Added
- Implemented tenant projections for the support domain, introducing
  read‑only projections for tenant users and tenant groups.  Added
  corresponding SQLAlchemy models (`TenantUserShadow` and
  `TenantGroupShadow`), Pydantic schemas, service layer functions,
  and tenant‑scoped API routes (`/tenants/{tenant_id}/tenant-users` and
  `/tenants/{tenant_id}/tenant-groups`).
- Updated FastAPI wiring in `main_api.py` to include the new routers
  and imported the modules for model registration in `app/core/db.py`.
- Added tests (`tests/test_support_tenant_shadows.py`) verifying
  routing behaviour, service invocation and the absence of write
  endpoints for these projections.

### Changed
- Extended `app/domain/models/__init__.py` and `app/domain/schemas/__init__.py`
  exports to include the new projection models and schemas.
- Updated `app/api/routes/__init__.py` to expose the new routers.

### Tests
- Added `tests/test_support_tenant_shadows.py` covering list and get
  endpoints for tenant user and group projections and ensuring
  missing write endpoints return HTTP 405.

### Notes
- The tenant projection endpoints are read‑only and do not emit
  messaging events.  They rely on asynchronous synchronisation from
  the tenant management service and are intended primarily for UI
  lookups and foreign key validation.

## [2025-12-31] – DB error handling and rollback standardization

### Added
- Introduced `commit_or_raise` helper in `app/domain/services/common_service.py` to centralize transaction commits.
  The helper commits the SQLAlchemy session, optionally refreshes an ORM instance, and handles all database
  exceptions by rolling back and translating them into meaningful `HTTPException` instances.
- Added a `CONSTRAINT_HINTS` dictionary and improved `_http_exception_from_db_error` to sanitize check
  constraint error messages and include field/allowed value hints for known constraints.
- Created `error_handling_implementation.md` documenting the rationale behind the new helper, the
  sanitization approach, and the steps taken to apply the pattern across services.
- Added tests in `tests/test_common_service_db_errors.py` covering translation of unique and check
  constraint violations and verifying that `commit_or_raise` rolls back sessions appropriately.

### Changed
- Replaced all direct calls to `db.commit()` in `company_service.py`, `contact_service.py`, and
  `lead_service.py` with calls to `commit_or_raise`, ensuring consistent rollback and error translation.
- Updated service functions to supply descriptive `action` names to `commit_or_raise` and passed
  ORM instances to refresh when previously used.
- Sanitized check constraint violations to remove row data from error responses and added constraint
  hints where available.

### Tests
- Added `tests/test_common_service_db_errors.py` verifying the new helper and error translation.
- Updated service tests to accommodate the new error handling (if necessary) and ensure that unique
  and check constraint violations return HTTP 409 and HTTP 422, respectively.

## [2025-12-30] – Postgres-in-Docker Test Harness

### Added
- Introduced a comprehensive test infrastructure that runs database tests
  against a temporary Postgres instance started via Docker Compose.  A new
  `docker-compose.test.yml` defines the test container and mounts the
  existing `init-database.sql` to provision the database and users.
- Added `test-liquibase.properties` to point Liquibase at the test
  database.  Migrations are applied once per test session only when
  tests are marked with `@pytest.mark.liquibase`.
- Added a dedicated `pytest.ini` configuring custom markers (`postgres`,
  `liquibase`, `integration`) and enabling terse output.
- Rewrote `tests/conftest.py` to start/stop the Postgres container,
  apply migrations, create a SQLAlchemy engine, provide transactional
  sessions, and supply a FastAPI `TestClient` that overrides the
  database dependency.  Pure unit tests continue to run without
  starting Docker.
- Added a new test `tests/test_pg_jsonb.py` verifying that JSONB
  columns are usable under Postgres.

### Changed
- Updated `tests/test_contact.py` to use the tenant‑scoped API
  (`/tenants/{tenant_id}/contacts`) and the appropriate nested payload
  structure for phones and emails.  Contact tests now send the user
  identity via the `X-User` header and apply updates via JSON Patch.
- Removed the old SQLite-based test setup; database tests now use
  Postgres exclusively and run within transactions that roll back
  after each test.

### Tests
- All contact API tests are marked with `@pytest.mark.postgres` and
  `@pytest.mark.liquibase` to trigger the Docker container and
  migrations.  A new PG-specific test ensures JSONB columns work
  correctly.

### Notes
- To run the full test suite locally, ensure Docker is installed and
  available.  Then execute `python -m pytest`.  To run only unit
  tests without starting Docker, use `pytest -m "not postgres"`.

## [2025-12-28] – Fix Pydantic Config & Telemetry Initialization

### Added
- New test `tests/test_telemetry.py` ensuring tracing initialization fails gracefully when the OTLP exporter endpoint is not set.

### Changed
- Updated all Pydantic read schemas (`ContactRead`, `CompanyRead`, `PipelineRead`, `PipelineStageRead`, `DealRead`, `ActivityRead`, `ListRead`, `ListMembershipRead`, `AssociationRead`) to use `ConfigDict(from_attributes=True)` instead of the deprecated class‐based `Config.orm_mode`.
- Modified `app/core/telemetry.py` to disable OTLP exporter creation when `OTEL_EXPORTER_OTLP_ENDPOINT` is not configured, preventing connection errors during tests and local development.

### Tests
- Existing tests remain unchanged and continue to pass.
- Added test coverage for graceful telemetry initialization via `tests/test_telemetry.py`.

### Notes
- These changes remove Pydantic v2 deprecation warnings and prevent `ConnectionRefusedError` and logging errors that occurred when the OTLP exporter attempted to connect to `localhost:4318` without a running collector.