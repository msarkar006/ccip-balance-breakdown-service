# Graph Report - ccip-balance-breakdown-service  (2026-11-26)

## Corpus Check
- 257 files · ~81,371 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 37 file(s) not represented in the graph (top: .scss 21, (none) 8, .tsbuildinfo 2)

## Summary
- 2383 nodes · 4868 edges · 195 communities (79 shown, 116 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 318 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e7bf1499`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CCIP Balance Breakdown Service
- test_pipeline_migration_parity.py
- AppUser
- Customer
- get_balance_transfers
- auth-context.tsx
- compilerOptions
- balance_breakdowns_service.py
- .get_account_overview
- steps
- typing
- test_get_money_transfer_detail_not_found
- Any
- database
- support_diagnostics.py
- StatusTrackingService
- backend
- auth/auth.py
- package.json
- TASK-4 Handoff: Balance Breakdown and Balance Transfer Offers
- compilerOptions
- scripts
- @playwright/test
- ccip-balance-breakdown-service
- test_offers.py
- TASK-3: Backend Feature B1 - Account Overview and Multi-Account Context
- sqlalchemy_orm
- UserSession
- conftest.py
- money_transfers_service.py
- TASK-10 Handoff Documentation: Support Diagnostics and Health Endpoints
- PaymentService
- RewardsOffersPage.tsx
- TransactionHistoryPage.tsx
- HighRiskWritePipeline
- AuthorizationError
- direct_debits.py
- payments_service.py
- middleware/auth.py
- require_step_up
- PaymentsRepository
- dependencies
- test_health_endpoints.py
- test_auth_session_revoke.py
- .get_tracker_view
- TASK-7 Handoff: Backend Feature B5 - Balance Transfer and Money Transfer Tracking
- direct_debits_service.py
- IdentityStepUpAdapter
- BalanceTransferInitiationPipeline
- balance_transfers.py
- TASK-9 Handoff: Instalment Plans and Unified Status Tracker
- PaymentManagementPage.tsx
- TransactionService
- 20261126_1400_add_balance_category_fields.py
- audit_service.py
- eslint.config.js
- start.sh
- FraudAndRiskAdapter
- test_account
- docker-entrypoint.sh
- test_balance_transfers/test_initiation.py
- devDependencies
- test_money_transfers/test_initiation.py
- BalanceTransferRailAdapter
- stop.sh
- api-client.ts
- @vitejs/plugin-react
- NotFoundError
- @carbon/react
- test_rewards.py
- test_auth_step_up.py
- CreditCardAccount
- BalanceBreakdownPage.tsx
- test_payee.py
- test-setup.ts
- 20261126_0001_001_create_core_tables.py
- .get_payments
- auth.ts
- 20261126_0002_002_create_account_and_card_tables.py
- settings.py
- 20261126_0003_003_create_transaction_and_payment_tables.py
- 20261126_0004_004_create_transfer_and_dd_tables.py
- 20261126_0005_005_create_balance_and_rewards_tables.py
- 20261126_0006_006_create_tracking_and_audit_tables.py
- 20261126_1316_ac8abdc5e7f1_add_selected_account_id_to_user_sessions.py
- RefreshOutcome
- BalanceTransferService
- Payment
- .select_account
- test_payments.py
- AuthRepository
- PaymentRailAdapter
- AuditService
- DirectDebitRepository
- MoneyTransferRailAdapter
- get_money_transfers
- MoneyTransfersRepository
- test_accounts_overview.py
- test_accounts_selection.py
- test_auth_logout.py
- test_get_balance_transfer_detail_not_found
- test_accounts_list.py
- AuthenticationError
- .record
- .initiate_transfer
- fastapi_testclient
- MoneyTransferService
- End-to-End Integration Tests
- RateLimitError
- Test Results Summary
- TransactionsRepository
- Backend Test Suite
- Test Execution Commands
- Acceptance Criteria Status
- Frontend Test Suite
- Test Coverage Summary
- TASK-5 Handoff: Backend Feature B3 - Transactions and Payment History
- CorrelationIDMiddleware
- RateLimitMiddleware
- TransactionListResponse
- DirectDebitChangeRequest
- register_error_handlers
- get_tracker_detail
- Backend Flows
- Request/Response Shapes
- AppError
- initiate_payment
- Module Structure
- test_get_current_breakdown_not_found
- test_get_category_detail_success
- test_get_category_detail_not_found
- test_get_breakdown_requires_auth
- test_get_current_breakdown_success
- test_get_balance_transfers_requires_auth
- test_get_money_transfers_requires_auth

## God Nodes (most connected - your core abstractions)
1. `CreditCardAccount` - 94 edges
2. `AppUser` - 84 edges
3. `Customer` - 54 edges
4. `Base` - 45 edges
5. `TrackingEvent` - 40 edges
6. `Payment` - 37 edges
7. `NotFoundError` - 37 edges
8. `StatusTrackingService` - 35 edges
9. `BalanceTransfer` - 32 edges
10. `MoneyTransfer` - 28 edges

## Surprising Connections (you probably didn't know these)
- `Balance Breakdown Retrieval` --references--> `FreshnessAndSyncService`  [INFERRED]
  .handoff/TASK-4.md → backend/app/sync/sync_service.py
- `Direct Debit Change Flow (POST /api/v1/direct-debits/change-requests)` --references--> `require_step_up()`  [INFERRED]
  .handoff/TASK-6.md → backend/app/middleware/auth.py
- `Payment Initiation Flow (POST /api/v1/payments)` --references--> `require_step_up()`  [INFERRED]
  .handoff/TASK-6.md → backend/app/middleware/auth.py
- `Payment Endpoints` --references--> `DirectDebitCoverageResponse`  [INFERRED]
  .handoff/TASK-6.md → backend/app/direct_debits/direct_debits_schemas.py
- `Money Transfer Detail Flow` --references--> `MoneyTransferDetailResponse`  [INFERRED]
  .handoff/TASK-7.md → backend/app/money_transfers/money_transfers_schemas.py

## Import Cycles
- None detected.

## Communities (195 total, 116 thin omitted)

### Community 0 - "CCIP Balance Breakdown Service"
Cohesion: 0.05
Nodes (43): 1. Local Development (Recommended), 2. Docker Deployment (SQLite), 3. Docker Deployment (PostgreSQL), Accounts, API Documentation, Apply Migrations, Authentication, Backend (+35 more)

### Community 1 - "test_pipeline_migration_parity.py"
Cohesion: 0.09
Nodes (21): get_url(), run_migrations_offline(), run_migrations_online(), _alembic(), _annotation_kind(), _column_kind(), _env_py_text(), _foreign_key() (+13 more)

### Community 2 - "AppUser"
Cohesion: 0.05
Nodes (25): hash_password(), verify_password(), is_support_user(), AppUser, require_support_role(), auth_client(), test_login_inactive_user(), test_login_invalid_credentials() (+17 more)

### Community 3 - "Customer"
Cohesion: 0.08
Nodes (16): Customer, test_get_instalment_plan_detail_not_found(), test_get_instalment_plan_detail_with_linked_category(), test_get_instalment_plan_detail_without_linked_category(), test_list_instalment_plans_empty(), test_list_instalment_plans_pagination(), test_list_instalment_plans_requires_auth(), test_list_instalment_plans_success() (+8 more)

### Community 4 - "get_balance_transfers"
Cohesion: 0.14
Nodes (3): get_balance_transfer_detail(), get_balance_transfers(), initiate_balance_transfer()

### Community 5 - "auth-context.tsx"
Cohesion: 0.13
Nodes (21): App(), AccountSelector(), RequireAuth(), Header(), HeaderProps, Layout(), LayoutProps, Sidebar() (+13 more)

### Community 6 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 7 - "balance_breakdowns_service.py"
Cohesion: 0.08
Nodes (7): get_category_detail(), get_current_balance_breakdown(), BalanceBreakdownsRepository, BalanceCategoryItem, FreshnessInfo, SourceLink, BalanceBreakdownService

### Community 9 - "steps"
Cohesion: 0.06
Nodes (36): runs-on, services, steps, DATABASE_URL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, runs-on (+28 more)

### Community 10 - "typing"
Cohesion: 0.03
Nodes (25): AccountListItem, AccountListResponse, AccountOverviewResponse, AccountSelectionRequest, AccountSelectionResponse, CreditCardDetail, get_logger(), get_instalment_plan_detail() (+17 more)

### Community 12 - "Any"
Cohesion: 0.08
Nodes (3): ValidationError, MoneyTransferInitiationPipeline, PaymentInitiationPipeline

### Community 13 - "database"
Cohesion: 0.10
Nodes (19): PIP_TARGET, build, depends_on, environment, args, context, environment, image (+11 more)

### Community 14 - "support_diagnostics.py"
Cohesion: 0.11
Nodes (12): diagnostic_lookup(), health_live(), health_ready(), operational_summary(), DiagnosticEvent, DiagnosticLookupRequest, DiagnosticLookupResponse, EscalationContext (+4 more)

### Community 15 - "StatusTrackingService"
Cohesion: 0.11
Nodes (8): refresh_tracker_item(), TrackerDetailResponse, TrackerEscalation, TrackerFreshness, TrackerGuidance, TrackerItem, TrackerRefreshResponse, StatusTrackingService

### Community 16 - "backend"
Cohesion: 0.12
Nodes (17): build, environment, ports, volumes, x-preview-port, context, dockerfile, DATABASE_URL (+9 more)

### Community 17 - "auth/auth.py"
Cohesion: 0.18
Nodes (6): CurrentUserResponse, LoginRequest, LoginResponse, SessionRevokeResponse, StepUpRequest, StepUpResponse

### Community 18 - "package.json"
Cohesion: 0.12
Nodes (16): @carbon/styles@^1.72.0, jsdom@^25.0.1, @types/node@^22.9.3, @types/react@^18.3.0, typescript@^5.6.0, engines, node, name (+8 more)

### Community 21 - "TASK-4 Handoff: Balance Breakdown and Balance Transfer Offers"
Cohesion: 0.09
Nodes (22): Account ACC-1001 (****1001), Account ACC-1001 Offers, Backend Flows, Balance Breakdown Response, Balance Breakdown Retrieval, Balance Breakdown Tests (11 tests), Balance Breakdowns, Category Detail Response (+14 more)

### Community 22 - "compilerOptions"
Cohesion: 0.22
Nodes (8): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, strict, include

### Community 23 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, type-check

### Community 32 - "test_offers.py"
Cohesion: 0.09
Nodes (11): test_account(), test_customer(), test_list_offers_all(), test_list_offers_by_context_balance_transfer(), test_list_offers_by_context_instalment(), test_list_offers_by_context_rewards(), test_list_offers_empty_results(), test_list_offers_invalid_context() (+3 more)

### Community 33 - "TASK-3: Backend Feature B1 - Account Overview and Multi-Account Context"
Cohesion: 0.06
Nodes (31): Account Endpoints, Account Selection Flow, Authentication Endpoints, Backend Flows, DELETE /api/v1/auth/sessions/{session_id}, Dependencies Added, GET /api/v1/accounts, GET /api/v1/accounts/{id}/overview (+23 more)

### Community 35 - "sqlalchemy_orm"
Cohesion: 0.04
Nodes (34): Base, AuditLog, BalanceBreakdown, BalanceCategory, BalanceTransfer, CreditCard, InstalmentPlan, MoneyTransfer (+26 more)

### Community 37 - "conftest.py"
Cohesion: 0.22
Nodes (3): client(), db_session(), _fresh_schema()

### Community 38 - "money_transfers_service.py"
Cohesion: 0.14
Nodes (11): GuidanceInfo, MoneyTransferDetailResponse, MoneyTransferInitiationRequest, MoneyTransferInitiationResponse, MoneyTransferListItem, MoneyTransferListResponse, PayeeInfo, PayeeListItem (+3 more)

### Community 39 - "TASK-10 Handoff Documentation: Support Diagnostics and Health Endpoints"
Cohesion: 0.06
Nodes (30): Backend Flows, Dependencies, Diagnostic Lookup Flow, DiagnosticLookupRequest, DiagnosticLookupResponse, Freshness & Synchronization, Future Enhancements, Health Endpoints Flow (+22 more)

### Community 40 - "PaymentService"
Cohesion: 0.12
Nodes (6): cancel_payment(), get_payment_detail(), get_payment_guidance(), get_payments(), TrackerMilestone, PaymentService

### Community 41 - "RewardsOffersPage.tsx"
Cohesion: 0.20
Nodes (10): OfferList(), OfferListProps, RewardsSummary(), RewardsSummaryProps, RewardsOffersPage(), FreshnessInfo, Offer, RewardsProgramme (+2 more)

### Community 42 - "TransactionHistoryPage.tsx"
Cohesion: 0.16
Nodes (9): AccountSelectorProps, Account, AccountListResponse, AccountSelectionRequest, AccountSelectionResponse, CreditCard, Transaction, FreshnessInfo (+1 more)

### Community 43 - "HighRiskWritePipeline"
Cohesion: 0.06
Nodes (21): HighRiskWritePipeline, Backend Flows, Balance Transfer Initiation, Balance Transfer Initiation, Balance Transfer Initiation Request, Balance Transfer Initiation Response, Demo Payees (Customer CUST-001, Account ACC-1001), Demo Rewards Programme (+13 more)

### Community 46 - "direct_debits.py"
Cohesion: 0.12
Nodes (7): create_change_request(), get_direct_debits(), ChangeRequestRequest, ChangeRequestResponse, DirectDebitListItem, DirectDebitListResponse, Direct Debit Endpoints

### Community 47 - "payments_service.py"
Cohesion: 0.15
Nodes (9): PaymentCancellationResponse, PaymentDetailResponse, PaymentGuidanceResponse, PaymentInitiationRequest, PaymentInitiationResponse, PaymentListResponse, PaymentResponse, Payment Endpoints (+1 more)

### Community 48 - "middleware/auth.py"
Cohesion: 0.07
Nodes (9): BalanceBreakdownResponse, CategoryDetailResponse, get_db(), lifespan(), configure_logging(), mask_pii(), root(), get_current_user() (+1 more)

### Community 49 - "require_step_up"
Cohesion: 0.10
Nodes (20): require_step_up(), AuditService, Backend Flows, Direct Debit Change Flow (POST /api/v1/direct-debits/change-requests), DirectDebitService Coverage Derivation, GET /api/v1/direct-debits, GET /api/v1/payments/guidance, HighRiskWritePipeline (+12 more)

### Community 51 - "dependencies"
Cohesion: 0.17
Nodes (12): dependencies, @carbon/icons-react@^11.59.0, @carbon/react@^1.72.0, clsx@^2.1.1, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.0, tailwind-merge@^2.5.4 (+4 more)

### Community 53 - "test_health_endpoints.py"
Cohesion: 0.15
Nodes (5): test_health_live_always_ok(), test_health_live_no_auth_required(), test_health_ready_database_ok(), test_health_ready_database_unavailable(), test_health_ready_no_auth_required()

### Community 54 - "test_auth_session_revoke.py"
Cohesion: 0.23
Nodes (4): test_revoke_nonexistent_session(), test_revoke_session_success(), test_revoke_session_then_use_token(), test_revoke_session_without_auth()

### Community 60 - "TASK-7 Handoff: Backend Feature B5 - Balance Transfer and Money Transfer Tracking"
Cohesion: 0.09
Nodes (21): Backend Flows, Balance Transfer Detail Response, Balance Transfer List Response, Balance Transfers Domain, Guidance Object, Guidance Rules, Implementation Summary, Module Structure (+13 more)

### Community 63 - "direct_debits_service.py"
Cohesion: 0.13
Nodes (4): DirectDebitRailAdapter, StubDirectDebitRailAdapter, DirectDebitCoverageResponse, DirectDebitService

### Community 66 - "balance_transfers.py"
Cohesion: 0.13
Nodes (10): BalanceTransferDetailResponse, BalanceTransferInitiationRequest, BalanceTransferInitiationResponse, BalanceTransferListItem, BalanceTransferListResponse, GuidanceInfo, PromotionalContext, SourceLink (+2 more)

### Community 68 - "TASK-9 Handoff: Instalment Plans and Unified Status Tracker"
Cohesion: 0.08
Nodes (23): Backend Flows, Escalation Thresholds, Instalment Plan Visibility, Instalment Plans, Instalment Plans (ACC-1001), InstalmentPlanDetailResponse, InstalmentPlanListResponse, Mounted Endpoints (+15 more)

### Community 69 - "PaymentManagementPage.tsx"
Cohesion: 0.08
Nodes (31): BalanceSummary(), BalanceSummaryProps, CardStatus(), CardStatusProps, StepUpModal(), StepUpModalProps, CategoryList(), PaymentForm() (+23 more)

### Community 73 - "eslint.config.js"
Cohesion: 0.18
Nodes (10): @eslint/js@^9.15.0, eslint-plugin-react-hooks@^5.0.0, eslint-plugin-react-refresh@^0.4.14, globals@^15.12.0, typescript-eslint@^8.15.0, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh (+2 more)

### Community 77 - "start.sh"
Cohesion: 0.48
Nodes (6): check_prerequisites(), DATABASE_URL, find_available_port(), native_path(), port_in_use(), start.sh script

### Community 81 - "test_balance_transfers/test_initiation.py"
Cohesion: 0.25
Nodes (3): test_balance_transfer_initiation_happy_path(), test_balance_transfer_initiation_idempotency(), test_balance_transfer_initiation_missing_step_up()

### Community 82 - "devDependencies"
Cohesion: 0.12
Nodes (17): devDependencies, autoprefixer@^10.4.20, eslint@^9.15.0, @playwright/test@^1.48.0, postcss@^8.4.47, sass@^1.108.2, tailwindcss@^3.4.14, @testing-library/react@^16.0.0 (+9 more)

### Community 83 - "test_money_transfers/test_initiation.py"
Cohesion: 0.25
Nodes (3): test_money_transfer_initiation_happy_path(), test_money_transfer_initiation_idempotency(), test_money_transfer_initiation_missing_step_up()

### Community 96 - "api-client.ts"
Cohesion: 0.08
Nodes (28): TrackerTable(), TrackerTableProps, apiClient, ApiError, clearAuthToken(), getAuthToken(), request(), TrackingActivityPage() (+20 more)

### Community 97 - "@vitejs/plugin-react"
Cohesion: 0.33
Nodes (4): vite@^6.0.0, @vitejs/plugin-react@^4.3.0, vite, @vitejs/plugin-react

### Community 98 - "NotFoundError"
Cohesion: 0.15
Nodes (7): login(), logout(), revoke_session(), LogoutResponse, AuthService, step_up(), NotFoundError

### Community 100 - "@carbon/react"
Cohesion: 0.09
Nodes (29): BalanceTransferForm(), BalanceTransferFormProps, MoneyTransferForm(), MoneyTransferFormProps, PayeeSelectorProps, getGuidanceMessage(), getStatusTagKind(), isBalanceTransfer() (+21 more)

### Community 101 - "test_rewards.py"
Cohesion: 0.28
Nodes (4): test_get_rewards_summary_offers_filtered(), test_get_rewards_summary_with_programme(), test_get_rewards_summary_without_programme(), Known Issues

### Community 102 - "test_auth_step_up.py"
Cohesion: 0.23
Nodes (4): test_step_up_invalid_password(), test_step_up_success(), test_step_up_verification_stored(), test_step_up_without_auth()

### Community 103 - "CreditCardAccount"
Cohesion: 0.08
Nodes (17): CreditCardAccount, DirectDebitMandate, test_audit_log_created_during_direct_debit_change(), test_audit_log_created_during_payment(), test_change_request_happy_path(), test_change_request_idempotency(), test_change_request_step_up_required(), test_direct_debit_coverage_cannot_be_confirmed() (+9 more)

### Community 110 - "BalanceBreakdownPage.tsx"
Cohesion: 0.25
Nodes (6): CategoryListProps, BalanceBreakdown, BalanceBreakdownResponse, BalanceCategory, FreshnessInfo, SourceLink

### Community 115 - "auth.ts"
Cohesion: 0.50
Nodes (3): LoginRequest, LoginResponse, User

### Community 125 - "Payment"
Cohesion: 0.13
Nodes (9): Payment, test_get_tracker_detail_with_escalation(), test_get_tracker_detail_with_timeline(), test_get_tracker_list_pagination(), test_get_tracker_list_success(), test_tracker_detail_not_found(), test_tracker_list_requires_auth(), test_tracker_refresh_success() (+1 more)

### Community 126 - ".select_account"
Cohesion: 0.13
Nodes (4): get_account_overview(), list_accounts(), select_account(), AccountOverviewService

### Community 127 - "test_payments.py"
Cohesion: 0.15
Nodes (9): test_get_payment_detail_requires_auth(), test_get_payment_detail_with_timeline(), test_get_payment_not_found(), test_get_payments_empty_state(), test_get_payments_requires_auth(), test_get_payments_success(), test_payment_can_cancel_logic(), test_payment_guidance_messages() (+1 more)

### Community 129 - "PaymentRailAdapter"
Cohesion: 0.17
Nodes (3): PaymentRailAdapter, StubPaymentRailAdapter, Adapters

### Community 130 - "AuditService"
Cohesion: 0.16
Nodes (3): AuditService, test_audit_service_financial_7y_retention(), test_audit_service_record()

### Community 133 - "get_money_transfers"
Cohesion: 0.29
Nodes (3): get_money_transfer_detail(), get_money_transfers(), get_payees()

### Community 135 - "test_accounts_overview.py"
Cohesion: 0.24
Nodes (4): test_get_account_overview_no_cards(), test_get_account_overview_not_found(), test_get_account_overview_success(), test_get_account_overview_without_auth()

### Community 136 - "test_accounts_selection.py"
Cohesion: 0.23
Nodes (4): test_clear_account_selection(), test_select_account_success(), test_select_account_without_auth(), test_select_nonexistent_account()

### Community 137 - "test_auth_logout.py"
Cohesion: 0.27
Nodes (3): test_logout_success(), test_logout_twice(), test_logout_without_auth()

### Community 140 - "test_accounts_list.py"
Cohesion: 0.24
Nodes (3): test_list_accounts_empty(), test_list_accounts_success(), test_list_accounts_without_auth()

### Community 142 - "AuthenticationError"
Cohesion: 0.20
Nodes (3): AuthenticationError, get_current_user_session(), verify_account_ownership()

### Community 147 - "End-to-End Integration Tests"
Cohesion: 0.25
Nodes (8): E2E Test Environment, End-to-End Integration Tests, Journey 1: New Payment Submission, Journey 2: Balance Transfer Initiation, Journey 3: Money Transfer Initiation, Journey Test Specifications, Test Framework, Wireframe E2E Tests (from earlier tasks)

### Community 150 - "Test Results Summary"
Cohesion: 0.29
Nodes (6): Conclusion, Future Enhancements, Immediate Actions, Overview, Recommendations, Test Results Summary

### Community 152 - "Backend Test Suite"
Cohesion: 0.33
Nodes (6): Backend Test Suite, Backend Test Summary, Critical Path Coverage, Sample Test Run (Core Domains), Test Coverage by Domain, Test Framework

### Community 153 - "Test Execution Commands"
Cohesion: 0.33
Nodes (6): Backend Tests (Core Domains), Backend Tests (Full Suite), E2E Journey Tests (Written, Environment Issue Prevents Execution), Frontend Unit Tests, Full E2E Suite (All Wireframes + Journeys), Test Execution Commands

### Community 154 - "Acceptance Criteria Status"
Cohesion: 0.40
Nodes (5): Acceptance Criteria Status, Backend Tests (Requirement: validate all backend pytest tests pass), E2E Journey Tests (Requirement: 3 journey specs for core user flows), Frontend Tests (Requirement: validate all frontend vitest tests pass), Wireframe E2E Tests (Requirement: verify existing wireframe specs pass)

### Community 155 - "Frontend Test Suite"
Cohesion: 0.40
Nodes (5): Component Test Coverage, Frontend Test Suite, Frontend Test Summary, Test Coverage by Component, Test Framework

### Community 156 - "Test Coverage Summary"
Cohesion: 0.50
Nodes (4): Backend Coverage, Frontend Coverage, Integration Coverage, Test Coverage Summary

### Community 157 - "TASK-5 Handoff: Backend Feature B3 - Transactions and Payment History"
Cohesion: 0.25
Nodes (7): Dependencies, Payment IDs (account ACC-1001), Router Registration, Seed Data, Seed Data Updates, TASK-5 Handoff: Backend Feature B3 - Transactions and Payment History, Transaction IDs (account ACC-1001)

### Community 162 - "TransactionListResponse"
Cohesion: 0.29
Nodes (4): TransactionListResponse, TransactionResponse, Mounted Endpoints, Transaction Endpoints

### Community 167 - "Backend Flows"
Cohesion: 0.40
Nodes (5): Backend Flows, Payment Detail Flow, Payment History Flow, Status Tracking Stub, Transaction Query Flow

### Community 168 - "Request/Response Shapes"
Cohesion: 0.40
Nodes (5): Payment Detail Response, Payment List Response, Request/Response Shapes, TrackerMilestone, Transaction List Response

### Community 171 - "Module Structure"
Cohesion: 0.50
Nodes (4): Module Structure, Payments Domain, Status Tracker Domain (stub), Transactions Domain

## Knowledge Gaps
- **2 isolated node(s):** `ccip-balance-breakdown-service`, `DATABASE_URL`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1212 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **116 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CreditCardAccount` connect `CreditCardAccount` to `AppUser`, `Customer`, `test_accounts_overview.py`, `.get_account_overview`, `test_accounts_selection.py`, `test_accounts_list.py`, `support_diagnostics.py`, `test_offers.py`, `sqlalchemy_orm`, `money_transfers_service.py`, `payments_service.py`, `middleware/auth.py`, `direct_debits_service.py`, `test_account`, `test_balance_transfers/test_initiation.py`, `test_money_transfers/test_initiation.py`, `BalanceTransferRailAdapter`, `test_rewards.py`, `test_payee.py`, `Payment`, `test_payments.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `CreditCardAccount` (e.g. with `test_all_models_instantiate()` and `test_credit_card_account_foreign_key()`) actually correct?**
  _`CreditCardAccount` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ccip-balance-breakdown-service`, `DATABASE_URL` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CCIP Balance Breakdown Service` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._
- **Why does `AppUser` connect `AppUser` to `AuthRepository`, `get_balance_transfers`, `get_money_transfers`, `balance_breakdowns_service.py`, `.get_account_overview`, `typing`, `.login`, `AuthenticationError`, `StatusTrackingService`, `.initiate_transfer`, `support_diagnostics.py`, `sqlalchemy_orm`, `UserSession`, `get_tracker_detail`, `money_transfers_service.py`, `conftest.py`, `PaymentService`, `initiate_payment`, `direct_debits.py`, `payments_service.py`, `middleware/auth.py`, `require_step_up`, `balance_transfers.py`, `TransactionService`, `BalanceTransferRailAdapter`, `NotFoundError`, `.select_account`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppUser` (e.g. with `test_app_user_model_crud()` and `test_user_id_is_integer_with_autoincrement()`) actually correct?**
  _`AppUser` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_pipeline_migration_parity.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08527131782945736 - nodes in this community are weakly interconnected._