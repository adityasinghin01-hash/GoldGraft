/* Generated from Python contracts. Do not edit. */

export type CreatedAt = string;
export type EvidenceRefs = string[];
export type GraftId = string;
export type HaltedAgent = string | null;
export type Id = string;
export type Message = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProducerKind".
 */
export type ProducerKind = "agent" | "service";
export type Model = string | null;
export type Name = string;
export type Version = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Severity".
 */
export type Severity = "CRITICAL" | "MAJOR" | "MINOR";
export type Assignee = string;
export type Attempt = number;
export type CreatedAt1 = string;
export type GraftId1 = string;
export type Id1 = string;
export type InputRefs = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Stage".
 */
export type Stage =
  | "CREATED"
  | "GATED"
  | "SURVEYED"
  | "BUILT"
  | "LINKS_PROVEN"
  | "DELIVERED"
  | "RECORDED"
  | "CONTRACTED"
  | "ATTACK_PLANNED"
  | "GRAFTED"
  | "PROVING"
  | "REPAIRING"
  | "CERTIFIED"
  | "PARTIAL"
  | "FAILED"
  | "PR_OPEN"
  | "MERGED"
  | "SHADOW"
  | "HEAL_1"
  | "HEAL_10"
  | "HEAL_50"
  | "LIVE_100"
  | "CLEANUP_PR"
  | "DONE"
  | "CUTBACK";
export type Agent = string;
export type CapUsd = number;
export type GraftId2 = string;
export type Model1 = string;
export type TokensCached = number;
export type TokensIn = number;
export type TokensOut = number;
export type Usd = number;
export type GraftId3 = string;
export type ItemsHash = string | null;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Kind".
 */
export type Kind =
  | "INTENT"
  | "APPROVE"
  | "AUTHORIZE"
  | "CAPTURE"
  | "VOID"
  | "SHOP_PAID"
  | "SHOP_PENDING"
  | "SHOP_UNPAID"
  | "NOTIFY"
  | "NOTIFY_VERIFIED"
  | "NOTIFY_REJECTED"
  | "REFUND"
  | "RECUR_SETUP"
  | "RECUR_CHARGE"
  | "ERROR";
export type Currency =
  | "AUD"
  | "BRL"
  | "CAD"
  | "CHF"
  | "CNY"
  | "CZK"
  | "DKK"
  | "EUR"
  | "GBP"
  | "HKD"
  | "HUF"
  | "ILS"
  | "JPY"
  | "MXN"
  | "MYR"
  | "NOK"
  | "NZD"
  | "PHP"
  | "PLN"
  | "RUB"
  | "SEK"
  | "SGD"
  | "THB"
  | "TWD"
  | "USD";
export type Minor = number;
export type Noise = string[];
export type OrderRef = string;
export type CaptureId = string | null;
export type DebugId = string | null;
export type LegacyToken = string | null;
export type OrderId = string | null;
export type ProfileId = string | null;
export type RefundId = string | null;
export type TxnId = string | null;
export type RawRef = string;
export type RunId = string;
export type ScenarioId = string;
export type Seq = number;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Source".
 */
export type Source = "SHOP_HTTP" | "SHOP_DB" | "PAYPAL_CALL" | "PAYPAL_LEDGER" | "NOTIFICATION";
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StatusNorm".
 */
export type StatusNorm = "COMPLETED" | "PENDING" | "DECLINED" | "REFUNDED" | "FAILED";
export type TMs = number;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Variant".
 */
export type Variant = "OLD" | "OLD_TWIN" | "NEW";
export type Branch = string;
export type CertId = string;
export type CommitNew = string;
export type CommitOld = string;
export type Tokens = number;
export type Usd1 = number;
export type IssuedAt = string;
export type LedgerRoot = string;
export type OtsProof = string | null;
export type CaptureId1 = string;
export type DebugId1 = string;
export type OrderId1 = string;
export type Scenario = string;
export type PaypalEvidence = PayPalEvidence[];
export type EquivalentDropped = number;
export type Killed = number;
export type MutantsTotal = number;
export type Score = number;
export type RekorEntry = string;
export type Repo = string;
export type NA = number;
export type Pass = number;
export type PassFixed = number;
export type Problem = number;
export type Scenarios = number;
export type Unverified = number;
export type Sha = string;
export type Workflow = string;
export type DepsBlocked = number;
export type InjectionAttemptsBlocked = number;
export type SecretsFound = number;
export type ShopId = string;
export type Signature = string;
export type MissesLearned = number;
export type Precision = number;
export type Recall = number;
export type Branch1 = string;
export type Commit = string;
export type PlanItemIds = string[];
export type Summary = string;
export type Changes = Change[];
export type CreatedAt2 = string;
export type GraftId4 = string;
export type Id2 = string;
export type OpenItemIds = string[];
export type NvpOk = boolean;
export type RestOk = boolean;
export type VersionMatch = boolean;
export type WebhookOk = boolean;
export type Repo1 = string | null;
export type SecretsRef = string;
export type ShopId1 = string;
export type Site = string | null;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Agreement".
 */
export type Agreement = "BOTH" | "CODE_ONLY" | "TRACE_ONLY";
export type CorrectFlow = string[];
export type CounterExamples = string[];
export type Id3 = string;
export type Predicate = string;
export type Code = string[];
export type Traces = string[];
export type Title = string;
export type Killed1 = boolean;
export type Mutants = string[];
export type Scenarios1 = string[];
export type Rules = Rule[];
export type ShopId2 = string;
export type CreatedAt3 = string;
export type EvidenceRefs1 = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JsonValue".
 */
export type JsonValue =
  | boolean
  | number
  | string
  | JsonValue[]
  | {
      [k: string]: JsonValue;
    }
  | null;
export type GraftId5 = string;
export type GroupBy = string[];
export type Id4 = string;
export type Metrics = string[];
export type Question = string;
export type Title1 = string;
export type CreatedAt4 = string;
export type EvidenceRefs2 = string[];
export type GraftId6 = string;
export type Id5 = string;
export type Language = string;
export type Operation = string;
export type Pattern = string;
export type ProvenRuns = number;
export type DriverStep1 = string;
export type ApiStep1 = string;
export type PaypalMockResponseCode = string;
export type Steps = (DriverStep | ApiStep | MockStep)[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "GuardEventKind".
 */
export type GuardEventKind = "ATTEMPT" | "APPROVED" | "CAPTURED" | "DECLINED" | "ERROR" | "REFUNDED";
export type GraftId7 = string;
export type LatencyMs = number;
export type LibVersion = string;
export type OrderRef1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Side".
 */
export type Side = "OLD" | "NEW";
export type ShopId3 = string;
export type Signature1 = string | null;
export type Ts = string;
export type FreezeWindowAdvice = string;
export type Amount = number;
export type Currency1 =
  | "AUD"
  | "BRL"
  | "CAD"
  | "CHF"
  | "CNY"
  | "CZK"
  | "DKK"
  | "EUR"
  | "GBP"
  | "HKD"
  | "HUF"
  | "ILS"
  | "JPY"
  | "MXN"
  | "MYR"
  | "NOK"
  | "NZD"
  | "PHP"
  | "PLN"
  | "RUB"
  | "SEK"
  | "SGD"
  | "THB"
  | "TWD"
  | "USD";
export type CustomerRef = string;
export type Cycle = string;
export type Id6 = string;
export type NextBilling = string | null;
export type Source1 = string;
export type Status = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffType".
 */
export type HandoffType = "BILLING_AGREEMENT" | "RECURRING_PROFILE";
export type Records = HandoffRecord[];
export type Duplicates = string[];
export type Inactive = number;
export type TotalsPerCurrency = Money[];
export type Amount1 = number;
export type Currency2 =
  | "AUD"
  | "BRL"
  | "CAD"
  | "CHF"
  | "CNY"
  | "CZK"
  | "DKK"
  | "EUR"
  | "GBP"
  | "HKD"
  | "HUF"
  | "ILS"
  | "JPY"
  | "MXN"
  | "MYR"
  | "NOK"
  | "NZD"
  | "PHP"
  | "PLN"
  | "RUB"
  | "SEK"
  | "SGD"
  | "THB"
  | "TWD"
  | "USD";
export type CustomerRef1 = string;
export type Cycle1 = string;
export type Id7 = string;
export type NextBilling1 = string | null;
export type Source2 = string;
export type Status1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealAction".
 */
export type HealAction = "HOLD" | "STEP_UP" | "CUTBACK";
export type FromStagePct = 0 | 1 | 10 | 50 | 100;
export type GraftId8 = string;
export type HardStop = string | null;
export type Reason = string;
export type NNew = number;
export type NOld = number;
export type ProbNewNotWorse = number;
export type SuccessNew = number;
export type SuccessOld = number;
export type Threshold = number;
export type ToStagePct = 0 | 1 | 10 | 50 | 100;
export type CreatedAt5 = string;
export type CutbackRequested = boolean;
export type EvidenceRefs3 = string[];
export type GraftId9 = string;
export type Id8 = string;
export type PauseRequested = boolean;
export type StagePct = 0 | 1 | 10 | 50 | 100;
export type Text = string;
export type CreatedAt6 = string;
export type GraftId10 = string;
export type Id9 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HeraldKind".
 */
export type HeraldKind = "GRAFT_CARD" | "PR_BODY" | "HANDOFF" | "VERDICT_EXPLAIN";
export type EntryHash = string;
export type JsonPointer = string;
export type Value = number;
export type NumbersUsed = LedgerNumber[];
export type Text1 = string;
export type Artifacts = string[];
export type Error = string | null;
export type Finished = string;
export type JobId = string;
export type LogsRef = string;
export type RateLimitPauses = number;
export type RawCaptureRefs = string[];
export type RunId1 = string;
export type Sha1 = string;
export type Workflow1 = string;
export type Started = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobStatus".
 */
export type JobStatus = "OK" | "FAILED" | "TIMEOUT" | "BLOCKED";
export type GraftId11 = string;
export type JobId1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobKind".
 */
export type JobKind = "BUILD" | "RECORD" | "PROVE" | "MUTANT_RUN" | "SHADOW" | "GAUNTLET";
export type MutantIds = string[];
export type ScenarioIds = string[];
export type SecretsRef1 = string;
export type ShopPackRef = string;
export type Signature2 = string | null;
export type BuildS = number;
export type RunS = number;
export type TotalS = number;
/**
 * @minItems 1
 */
export type Variants = [Variant, ...Variant[]];
export type CreatedAt7 = string;
export type GraftId12 = string;
export type Id10 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Lane".
 */
export type Lane = "FULL" | "NO-RUNTIME" | "NO-CODE";
export type Reason1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LedgerEntryV1".
 */
export type LedgerEntryV1 =
  | {
      entry_hash: EntryHash1;
      graft_id: GraftId13;
      inputs: Inputs;
      payload:
        | boolean
        | number
        | string
        | JsonValue[]
        | {
            [k: string]: JsonValue;
          }
        | null;
      payload_hash: PayloadHash;
      payload_ref?: never;
      prev_hash: PrevHash;
      producer: Producer;
      schema: Schema;
      seq: Seq1;
      ts: Ts1;
      type: EntryType;
    }
  | {
      entry_hash: EntryHash1;
      graft_id: GraftId13;
      inputs: Inputs;
      payload?: never;
      payload_hash: PayloadHash;
      payload_ref: string;
      prev_hash: PrevHash;
      producer: Producer;
      schema: Schema;
      seq: Seq1;
      ts: Ts1;
      type: EntryType;
    };
export type EntryHash1 = string;
export type GraftId13 = string;
export type Inputs = string[];
export type PayloadHash = string;
export type PrevHash = string;
export type Schema = string;
export type Seq1 = number;
export type Ts1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "EntryType".
 */
export type EntryType = "STAGE" | "ARTIFACT" | "MESSAGE" | "VERDICT" | "SWITCH" | "ALERT" | "COST";
export type HostedButtonId = string | null;
export type NewLinkUrl = string;
export type OldFormFields = {
  [k: string]: string;
} | null;
export type Page = string;
export type SnippetHtml = string;
export type Buttons = LinkButton[];
export type CaptureId2 = string;
export type Link = string;
export type OrderId2 = string;
export type Proofs = LinkProof[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "UntouchedKind".
 */
export type UntouchedKind = "Donate" | "Subscribe";
export type Untouched = UntouchedKind[];
export type Notes = string;
export type SignalFields = string[];
export type Source3 = string;
export type Currency3 =
  | "AUD"
  | "BRL"
  | "CAD"
  | "CHF"
  | "CNY"
  | "CZK"
  | "DKK"
  | "EUR"
  | "GBP"
  | "HKD"
  | "HUF"
  | "ILS"
  | "JPY"
  | "MXN"
  | "MYR"
  | "NOK"
  | "NZD"
  | "PHP"
  | "PLN"
  | "RUB"
  | "SEK"
  | "SGD"
  | "THB"
  | "TWD"
  | "USD";
export type Minor1 = number;
export type EquivalentSuspect = boolean;
export type Id11 = string;
export type KilledBy = string[];
export type File = string;
export type Line = number;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MutantOp".
 */
export type MutantOp = "M1" | "M2" | "M3" | "M4" | "M5" | "M6" | "M7" | "M8" | "M9" | "M10" | "M11" | "M12";
export type Patch = string;
export type Rule1 = string;
export type CreatedAt8 = string;
export type GraftId14 = string;
export type Id12 = string;
export type EquivalentSuspect1 = boolean;
export type Id13 = string;
export type KilledBy1 = string[];
export type Patch1 = string;
export type Rule2 = string;
export type Mutants1 = Mutant[];
export type UnguardedRuleIds = string[];
export type Fault = string;
export type RulesBroken = string[];
export type DeadlineNotes = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Family".
 */
export type Family =
  | "WPS"
  | "EC_NVP"
  | "EC_SOAP"
  | "DIRECT_PAYMENT"
  | "RECURRING_NVP"
  | "BILLING_AGREEMENT"
  | "IPN"
  | "PDT"
  | "CHECKOUT_JS_V4"
  | "JS_V5"
  | "REST_V1"
  | "SERVER_SDK_OLD"
  | "PAYFLOW"
  | "BUTTON_HOSTED";
export type FamiliesFound = Family[];
export type FilesOrPages = string[];
export type NextStep = string;
export type OfficialModernModuleAvailable = boolean | null;
export type EquivalentDropped1 = number;
export type Killed2 = number;
export type Score1 = number;
export type Total = number;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RawExchange".
 */
export type RawExchange =
  | {
      body_json?: never;
      body_text: string;
      db_change?: DbChange | null;
      direction: Direction;
      headers: Headers;
      method: Method;
      seq: Seq2;
      status?: Status2;
      t_ms: TMs1;
      url: Url;
    }
  | {
      body_json:
        | boolean
        | number
        | string
        | JsonValue[]
        | {
            [k: string]: JsonValue;
          }
        | null;
      body_text?: never;
      db_change?: DbChange | null;
      direction: Direction;
      headers: Headers;
      method: Method;
      seq: Seq2;
      status?: Status2;
      t_ms: TMs1;
      url: Url;
    }
  | {
      body_json?: never;
      body_text?: never;
      db_change?: DbChange | null;
      direction: "SHOP_DB_WRITE";
      headers: Headers;
      method: Method;
      seq: Seq2;
      status?: Status2;
      t_ms: TMs1;
      url: Url;
    };
export type After = {
  [k: string]: JsonValue;
} | null;
export type Before = {
  [k: string]: JsonValue;
} | null;
export type Table = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Direction".
 */
export type Direction =
  "SHOP_TO_PAYPAL" | "PAYPAL_TO_SHOP" | "BROWSER_TO_SHOP" | "PAYPAL_NOTIFY_TO_SHOP" | "SHOP_DB_WRITE";
export type Method = string;
export type Seq2 = number;
export type Status2 = number | null;
export type TMs1 = number;
export type Url = string;
export type Exchanges = RawExchange[];
export type GraftId15 = string;
export type RunId2 = string;
export type ScenarioId1 = string;
export type Confidence = number;
export type Compose = string;
export type Dockerfile = string;
export type DriverTemplate = string;
export type Seed = string;
export type AstShapeHash = string;
export type Framework = string;
export type Lang = string;
export type Id14 = string;
export type Provenance = string[];
export type Scenarios2 = string[];
export type Signature3 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecipeStatus".
 */
export type RecipeStatus = "QUARANTINE" | "ACTIVE" | "RETIRED";
export type Transform = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Lens".
 */
export type Lens = "code" | "runtime" | "site" | "account";
export type LensesRun = Lens[];
export type Selector = string;
export type Url1 = string;
export type Tcode = string;
export type Approve = (FileLocation | SiteLocation | AccountLocation)[];
export type Capture = (FileLocation | SiteLocation | AccountLocation)[];
export type Create = (FileLocation | SiteLocation | AccountLocation)[];
export type MarkPaid = (FileLocation | SiteLocation | AccountLocation)[];
export type Notify = (FileLocation | SiteLocation | AccountLocation)[];
export type Recurring = (FileLocation | SiteLocation | AccountLocation)[];
export type Refund = (FileLocation | SiteLocation | AccountLocation)[];
export type MatchedByStatic = number;
export type Misses = string[];
export type RuntimeCallsTotal = number;
export type ShopId4 = string;
export type Db = string;
export type Framework1 = string;
export type Lang1 = string;
export type Confidence1 = number;
export type Id15 = string;
export type Lenses = Lens[];
export type Live = boolean;
export type Location = FileLocation | SiteLocation | AccountLocation;
export type Operation1 = string;
export type PaypalOnly = boolean;
export type PaypalMappingId = string;
export type RestOp = string;
export type Touchpoints = Touchpoint[];
export type CorrectFlow1 = string[];
export type CounterExamples1 = string[];
export type Id16 = string;
export type Predicate1 = string;
export type Title2 = string;
export type BaseUrl = string;
export type Compose1 = string;
export type Seed1 = string;
export type FlakeFreeRuns = number;
export type PassesOnOld = boolean;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ScenarioFamily".
 */
export type ScenarioFamily =
  | "HAPPY"
  | "CANCEL"
  | "DECLINE"
  | "PAYER_ACTION"
  | "DOUBLE"
  | "LOST_RESPONSE"
  | "TAMPER"
  | "PENDING"
  | "REFUND"
  | "REFUND_TWICE"
  | "NOTIFY_FORGED"
  | "NOTIFY_DUP"
  | "RESTART"
  | "RENEWAL"
  | "EDGE_CURRENCY"
  | "PROPERTY";
export type Id17 = string;
export type Rules1 = string[];
export type Steps1 = (DriverStep | ApiStep | MockStep)[];
export type CreatedAt9 = string;
export type GraftId16 = string;
export type Id18 = string;
export type Id19 = string;
export type Rules2 = string[];
export type Steps2 = (DriverStep | ApiStep | MockStep)[];
export type Scenarios3 = Scenario1[];
export type UnguardedRuleIds1 = string[];
export type Touchpoints1 = Touchpoint[];
export type BuyerScript = string;
export type EnvNeeded = string[];
export type Framework2 = string;
export type HealthUrl = string;
export type Language1 = string;
export type Licence = string;
export type Name1 = string;
export type Port = number;
export type ScenariosSupported = string[];
export type ShopId5 = string;
export type Commit1 = string;
export type Repo2 = string;
export type Start = ComposeStart | CommandStart;
export type ComposeFile = string;
export type Command = string;
export type Name2 = string;
export type Attempt1 = number;
export type EvidenceRefs4 = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StageName".
 */
export type StageName = Stage | ("LANE_NO_CODE" | "LANE_NO_RUNTIME" | "LANE_MAP_ONLY");
export type GraftId17 = string;
export type Reason2 = string;
export type ExpiresAt = string;
export type GraftId18 = string;
export type OriginRules = string[];
export type Signature4 = string;
export type StagePct1 = 0 | 1 | 10 | 50 | 100;
export type Version1 = number;
export type Description = string;
export type Id20 = string;
export type MappingId = string;
export type Deltas = IntentDelta[];
export type Handoff = string[];
export type DeltaIds = string[];
export type MappingId1 = string;
export type PaypalOnly1 = boolean;
export type TargetOp = string;
export type Touchpoint1 = string;
export type Items = PlanItem[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PlanOrder".
 */
export type PlanOrder = "READ_BOTH" | "NEW_FLOWS_BEHIND_SWITCH" | "CLEANUP";
export type Order = PlanOrder[];
export type OriginRules1 = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PlanPath".
 */
export type PlanPath = "OFFICIAL_MODULE" | "REWRITE" | "LINKS";
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TargetExperience".
 */
export type TargetExperience1 =
  "V6" | "ORDERS_V2" | "WEBHOOKS" | "VAULT" | "PAY_LATER_MSG" | "PLACEMENT" | "AGENT_READY_CHECK";
export type TargetExperience = TargetExperience1[];
export type CreatedAt10 = string;
export type GraftId19 = string;
export type Id21 = string;
export type MutantIds1 = string[];
export type Reason3 = string;
export type RuleId = string;
export type ScenarioIds1 = string[];
export type DeltasApplied = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Grade".
 */
export type Grade = "PROBLEM" | "UNVERIFIED" | "PASS" | "PASS_FIXED" | "N/A";
export type NoiseMasked = string[];
export type ParityDiff = JsonValue[];
export type Evidence = string[];
export type Rule3 = string;
export type RuleHits = RuleHit[];
export type ScenarioId2 = string;

export interface GoldGraftContracts {
  AlertV1: AlertV1;
  AssignmentV1: AssignmentV1;
  BudgetRecordV1: BudgetRecordV1;
  CMELV1: CMELV1;
  CertificateV1: CertificateV1;
  ChangeListV1: ChangeListV1;
  ConnectionV1: ConnectionV1;
  ContractV1: ContractV1;
  DashboardSpecV1: DashboardSpecV1;
  DetectionRuleV1: DetectionRuleV1;
  DriverV1: DriverV1;
  GuardEventV1: GuardEventV1;
  HandoffPackV1: HandoffPackV1;
  HandoffRecordV1: HandoffRecordV1;
  HealDecisionV1: HealDecisionV1;
  HealNoteV1: HealNoteV1;
  HeraldTextV1: HeraldTextV1;
  JobResultV1: JobResultV1;
  JobSpecV1: JobSpecV1;
  LaneChangeV1: LaneChangeV1;
  LedgerEntryV1: LedgerEntryV1;
  LinksPackV1: LinksPackV1;
  MappingRowV1: MappingRowV1;
  MoneyV1: MoneyV1;
  MutantV1: MutantV1;
  MutantSetV1: MutantSetV1;
  MutationOperatorV1: MutationOperatorV1;
  ProbeResultV1: ProbeResultV1;
  ProofStrengthV1: ProofStrengthV1;
  RawCaptureV1: RawCaptureV1;
  RecipeV1: RecipeV1;
  RootMapV1: RootMapV1;
  RuleV1: RuleV1;
  RunnableShopV1: RunnableShopV1;
  ScenarioV1: ScenarioV1;
  ScenarioSetV1: ScenarioSetV1;
  ShopPackV1: ShopPackV1;
  StageChangeV1: StageChangeV1;
  SwitchConfigV1: SwitchConfigV1;
  TargetPlanV1: TargetPlanV1;
  TriangleRequestV1: TriangleRequestV1;
  VerdictV1: VerdictV1;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AlertV1".
 */
export interface AlertV1 {
  created_at: CreatedAt;
  evidence_refs: EvidenceRefs;
  graft_id: GraftId;
  halted_agent?: HaltedAgent;
  id: Id;
  message: Message;
  producer: Producer;
  severity: Severity;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Producer".
 */
export interface Producer {
  kind: ProducerKind;
  model?: Model;
  name: Name;
  version: Version;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AssignmentV1".
 */
export interface AssignmentV1 {
  assignee: Assignee;
  attempt: Attempt;
  created_at: CreatedAt1;
  graft_id: GraftId1;
  id: Id1;
  input_refs: InputRefs;
  producer: Producer;
  stage: Stage;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "BudgetRecordV1".
 */
export interface BudgetRecordV1 {
  agent: Agent;
  cap_usd: CapUsd;
  graft_id: GraftId2;
  model: Model1;
  tokens_cached: TokensCached;
  tokens_in: TokensIn;
  tokens_out: TokensOut;
  usd: Usd;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CMELV1".
 */
export interface CMELV1 {
  graft_id: GraftId3;
  items_hash?: ItemsHash;
  kind: Kind;
  money?: Money | null;
  noise: Noise;
  order_ref: OrderRef;
  pp: PayPalRefs;
  raw_ref: RawRef;
  run_id: RunId;
  scenario_id: ScenarioId;
  seq: Seq;
  source: Source;
  status_norm?: StatusNorm | null;
  t_ms: TMs;
  variant: Variant;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Money".
 */
export interface Money {
  currency: Currency;
  minor: Minor;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PayPalRefs".
 */
export interface PayPalRefs {
  capture_id?: CaptureId;
  debug_id?: DebugId;
  legacy_token?: LegacyToken;
  order_id?: OrderId;
  profile_id?: ProfileId;
  refund_id?: RefundId;
  txn_id?: TxnId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateV1".
 */
export interface CertificateV1 {
  branch: Branch;
  cert_id: CertId;
  commit_new: CommitNew;
  commit_old: CommitOld;
  cost: CertificateCost;
  issued_at: IssuedAt;
  ledger_root: LedgerRoot;
  ots_proof?: OtsProof;
  paypal_evidence: PaypalEvidence;
  proof_strength: CertificateStrength;
  rekor_entry: RekorEntry;
  repo: Repo;
  results: CertificateResults;
  runner_identity: RunnerIdentity;
  security: CertificateSecurity;
  shop_id: ShopId;
  signature: Signature;
  survey: CertificateSurvey;
  time: Time;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateCost".
 */
export interface CertificateCost {
  tokens: Tokens;
  usd: Usd1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PayPalEvidence".
 */
export interface PayPalEvidence {
  capture_id: CaptureId1;
  debug_id: DebugId1;
  order_id: OrderId1;
  scenario: Scenario;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateStrength".
 */
export interface CertificateStrength {
  equivalent_dropped: EquivalentDropped;
  killed: Killed;
  mutants_total: MutantsTotal;
  score: Score;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateResults".
 */
export interface CertificateResults {
  n_a: NA;
  pass: Pass;
  pass_fixed: PassFixed;
  problem: Problem;
  scenarios: Scenarios;
  unverified: Unverified;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RunnerIdentity".
 */
export interface RunnerIdentity {
  sha: Sha;
  workflow: Workflow;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateSecurity".
 */
export interface CertificateSecurity {
  deps_blocked: DepsBlocked;
  injection_attempts_blocked: InjectionAttemptsBlocked;
  secrets_found: SecretsFound;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateSurvey".
 */
export interface CertificateSurvey {
  misses_learned: MissesLearned;
  precision: Precision;
  recall: Recall;
}
export interface Time {
  [k: string]: number;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ChangeListV1".
 */
export interface ChangeListV1 {
  branch: Branch1;
  changes: Changes;
  created_at: CreatedAt2;
  graft_id: GraftId4;
  id: Id2;
  open_item_ids: OpenItemIds;
  producer: Producer;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Change".
 */
export interface Change {
  commit: Commit;
  plan_item_ids: PlanItemIds;
  summary: Summary;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConnectionV1".
 */
export interface ConnectionV1 {
  checks: ConnectionChecks;
  repo: Repo1;
  secrets_ref: SecretsRef;
  shop_id: ShopId1;
  site: Site;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConnectionChecks".
 */
export interface ConnectionChecks {
  nvp_ok: NvpOk;
  rest_ok: RestOk;
  version_match: VersionMatch;
  webhook_ok: WebhookOk;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ContractV1".
 */
export interface ContractV1 {
  rules: Rules;
  shop_id: ShopId2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Rule".
 */
export interface Rule {
  agreement: Agreement;
  correct_flow: CorrectFlow;
  counter_examples: CounterExamples;
  id: Id3;
  predicate: Predicate;
  severity: Severity;
  sources: RuleSources;
  title: Title;
  triangle: Triangle;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RuleSources".
 */
export interface RuleSources {
  code: Code;
  traces: Traces;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Triangle".
 */
export interface Triangle {
  killed: Killed1;
  mutants: Mutants;
  scenarios: Scenarios1;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DashboardSpecV1".
 */
export interface DashboardSpecV1 {
  created_at: CreatedAt3;
  evidence_refs: EvidenceRefs1;
  filters: Filters;
  graft_id: GraftId5;
  group_by: GroupBy;
  id: Id4;
  metrics: Metrics;
  producer: Producer;
  question: Question;
  title: Title1;
}
export interface Filters {
  [k: string]: JsonValue;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DetectionRuleV1".
 */
export interface DetectionRuleV1 {
  created_at: CreatedAt4;
  evidence_refs: EvidenceRefs2;
  graft_id: GraftId6;
  id: Id5;
  language: Language;
  operation: Operation;
  pattern: Pattern;
  producer: Producer;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DriverV1".
 */
export interface DriverV1 {
  proven_runs: ProvenRuns;
  selectors: Selectors;
  steps: Steps;
}
export interface Selectors {
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DriverStep".
 */
export interface DriverStep {
  driver_step: DriverStep1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ApiStep".
 */
export interface ApiStep {
  api_step: ApiStep1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MockStep".
 */
export interface MockStep {
  paypal_mock_response_code: PaypalMockResponseCode;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "GuardEventV1".
 */
export interface GuardEventV1 {
  event: GuardEventKind;
  graft_id: GraftId7;
  latency_ms: LatencyMs;
  lib_version: LibVersion;
  money?: Money | null;
  order_ref: OrderRef1;
  path: Side;
  paypal_ids?: PayPalRefs | null;
  shop_id: ShopId3;
  signature?: Signature1;
  ts: Ts;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffPackV1".
 */
export interface HandoffPackV1 {
  freeze_window_advice: FreezeWindowAdvice;
  records: Records;
  validation_summary: HandoffSummary;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffRecord".
 */
export interface HandoffRecord {
  amount: Amount;
  currency: Currency1;
  customer_ref: CustomerRef;
  cycle: Cycle;
  id: Id6;
  next_billing: NextBilling;
  source: Source1;
  status: Status;
  type: HandoffType;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffSummary".
 */
export interface HandoffSummary {
  counts: Counts;
  duplicates: Duplicates;
  inactive: Inactive;
  totals_per_currency: TotalsPerCurrency;
}
export interface Counts {
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffRecordV1".
 */
export interface HandoffRecordV1 {
  amount: Amount1;
  currency: Currency2;
  customer_ref: CustomerRef1;
  cycle: Cycle1;
  id: Id7;
  next_billing: NextBilling1;
  source: Source2;
  status: Status1;
  type: HandoffType;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealDecisionV1".
 */
export interface HealDecisionV1 {
  action: HealAction;
  from_stage_pct: FromStagePct;
  graft_id: GraftId8;
  hard_stop?: HardStop;
  reason: Reason;
  stats: HealStats;
  to_stage_pct: ToStagePct;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealStats".
 */
export interface HealStats {
  n_new: NNew;
  n_old: NOld;
  prob_new_not_worse: ProbNewNotWorse;
  success_new: SuccessNew;
  success_old: SuccessOld;
  threshold: Threshold;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealNoteV1".
 */
export interface HealNoteV1 {
  created_at: CreatedAt5;
  cutback_requested: CutbackRequested;
  evidence_refs: EvidenceRefs3;
  graft_id: GraftId9;
  id: Id8;
  pause_requested: PauseRequested;
  producer: Producer;
  stage_pct: StagePct;
  text: Text;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HeraldTextV1".
 */
export interface HeraldTextV1 {
  created_at: CreatedAt6;
  graft_id: GraftId10;
  id: Id9;
  kind: HeraldKind;
  numbers_used: NumbersUsed;
  producer: Producer;
  text: Text1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LedgerNumber".
 */
export interface LedgerNumber {
  entry_hash: EntryHash;
  json_pointer: JsonPointer;
  value: Value;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobResultV1".
 */
export interface JobResultV1 {
  artifacts: Artifacts;
  error?: Error;
  finished: Finished;
  job_id: JobId;
  logs_ref: LogsRef;
  rate_limit_pauses: RateLimitPauses;
  raw_capture_refs: RawCaptureRefs;
  runner_identity: JobRunnerIdentity;
  started: Started;
  status: JobStatus;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobRunnerIdentity".
 */
export interface JobRunnerIdentity {
  run_id: RunId1;
  sha: Sha1;
  workflow: Workflow1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobSpecV1".
 */
export interface JobSpecV1 {
  graft_id: GraftId11;
  job_id: JobId1;
  kind: JobKind;
  mutant_ids: MutantIds;
  scenario_ids: ScenarioIds;
  secrets_ref: SecretsRef1;
  shop_pack_ref: ShopPackRef;
  signature: Signature2;
  stage: Stage;
  timeouts: JobTimeouts;
  variants: Variants;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobTimeouts".
 */
export interface JobTimeouts {
  build_s: BuildS;
  run_s: RunS;
  total_s: TotalS;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LaneChangeV1".
 */
export interface LaneChangeV1 {
  created_at: CreatedAt7;
  graft_id: GraftId12;
  id: Id10;
  lane: Lane;
  producer: Producer;
  reason: Reason1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LinksPackV1".
 */
export interface LinksPackV1 {
  buttons: Buttons;
  proofs: Proofs;
  untouched: Untouched;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LinkButton".
 */
export interface LinkButton {
  hosted_button_id?: HostedButtonId;
  new_link_url: NewLinkUrl;
  old_form_fields?: OldFormFields;
  page: Page;
  snippet_html: SnippetHtml;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LinkProof".
 */
export interface LinkProof {
  capture_id: CaptureId2;
  link: Link;
  order_id: OrderId2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MappingRowV1".
 */
export interface MappingRowV1 {
  cmel_kind: Kind;
  notes: Notes;
  signal_fields: SignalFields;
  source: Source3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MoneyV1".
 */
export interface MoneyV1 {
  currency: Currency3;
  minor: Minor1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MutantV1".
 */
export interface MutantV1 {
  equivalent_suspect: EquivalentSuspect;
  id: Id11;
  killed_by: KilledBy;
  location: FileLocation;
  op: MutantOp;
  patch: Patch;
  rule: Rule1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "FileLocation".
 */
export interface FileLocation {
  file: File;
  line: Line;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MutantSetV1".
 */
export interface MutantSetV1 {
  created_at: CreatedAt8;
  graft_id: GraftId14;
  id: Id12;
  mutants: Mutants1;
  producer: Producer;
  unguarded_rule_ids: UnguardedRuleIds;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Mutant".
 */
export interface Mutant {
  equivalent_suspect: EquivalentSuspect1;
  id: Id13;
  killed_by: KilledBy1;
  location: FileLocation;
  op: MutantOp;
  patch: Patch1;
  rule: Rule2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MutationOperatorV1".
 */
export interface MutationOperatorV1 {
  fault: Fault;
  op: MutantOp;
  rules_broken: RulesBroken;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProbeResultV1".
 */
export interface ProbeResultV1 {
  deadline_notes: DeadlineNotes;
  families_found: FamiliesFound;
  files_or_pages: FilesOrPages;
  next_step: NextStep;
  official_modern_module_available?: OfficialModernModuleAvailable;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProofStrengthV1".
 */
export interface ProofStrengthV1 {
  equivalent_dropped: EquivalentDropped1;
  killed: Killed2;
  score: Score1;
  total: Total;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RawCaptureV1".
 */
export interface RawCaptureV1 {
  exchanges: Exchanges;
  graft_id: GraftId15;
  run_id: RunId2;
  scenario_id: ScenarioId1;
  variant: Variant;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DbChange".
 */
export interface DbChange {
  after: After;
  before: Before;
  key: Key;
  table: Table;
}
export interface Key {
  [k: string]: JsonValue;
}
export interface Headers {
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecipeV1".
 */
export interface RecipeV1 {
  confidence: Confidence;
  env?: RecipeEnv | null;
  fingerprint: Fingerprint;
  id: Id14;
  provenance: Provenance;
  scenarios: Scenarios2;
  signature: Signature3;
  status: RecipeStatus;
  transform: Transform;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecipeEnv".
 */
export interface RecipeEnv {
  compose: Compose;
  dockerfile: Dockerfile;
  driver_template: DriverTemplate;
  seed: Seed;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Fingerprint".
 */
export interface Fingerprint {
  ast_shape_hash: AstShapeHash;
  family: Family;
  framework: Framework;
  lang: Lang;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RootMapV1".
 */
export interface RootMapV1 {
  lenses_run: LensesRun;
  money_flow: MoneyFlow;
  recall_evidence: RecallEvidence;
  shop_id: ShopId4;
  stack: Stack;
  touchpoints: Touchpoints;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MoneyFlow".
 */
export interface MoneyFlow {
  approve: Approve;
  capture: Capture;
  create: Create;
  mark_paid: MarkPaid;
  notify: Notify;
  recurring: Recurring;
  refund: Refund;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SiteLocation".
 */
export interface SiteLocation {
  selector: Selector;
  url: Url1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AccountLocation".
 */
export interface AccountLocation {
  tcode: Tcode;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecallEvidence".
 */
export interface RecallEvidence {
  matched_by_static: MatchedByStatic;
  misses: Misses;
  runtime_calls_total: RuntimeCallsTotal;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Stack".
 */
export interface Stack {
  db: Db;
  framework: Framework1;
  lang: Lang1;
  versions: Versions;
}
export interface Versions {
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Touchpoint".
 */
export interface Touchpoint {
  confidence: Confidence1;
  family: Family;
  id: Id15;
  lenses: Lenses;
  live: Live;
  location: Location;
  money_30d?: Money | null;
  operation: Operation1;
  paypal_only: PaypalOnly;
  target: TouchpointTarget;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TouchpointTarget".
 */
export interface TouchpointTarget {
  paypal_mapping_id: PaypalMappingId;
  rest_op: RestOp;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RuleV1".
 */
export interface RuleV1 {
  agreement: Agreement;
  correct_flow: CorrectFlow1;
  counter_examples: CounterExamples1;
  id: Id16;
  predicate: Predicate1;
  severity: Severity;
  sources: RuleSources;
  title: Title2;
  triangle: Triangle;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RunnableShopV1".
 */
export interface RunnableShopV1 {
  base_url: BaseUrl;
  compose: Compose1;
  health: Health;
  image_digests: ImageDigests;
  seed: Seed1;
}
export interface Health {
  [k: string]: boolean;
}
export interface ImageDigests {
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ScenarioV1".
 */
export interface ScenarioV1 {
  assured: Assured;
  cart: Cart;
  expect: Expect;
  family: ScenarioFamily;
  id: Id17;
  rules: Rules1;
  steps: Steps1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Assured".
 */
export interface Assured {
  flake_free_runs: FlakeFreeRuns;
  passes_on_old: PassesOnOld;
}
export interface Cart {
  [k: string]: JsonValue;
}
export interface Expect {
  [k: string]: JsonValue;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ScenarioSetV1".
 */
export interface ScenarioSetV1 {
  created_at: CreatedAt9;
  graft_id: GraftId16;
  id: Id18;
  producer: Producer;
  scenarios: Scenarios3;
  unguarded_rule_ids: UnguardedRuleIds1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Scenario".
 */
export interface Scenario1 {
  assured: Assured;
  cart: Cart1;
  expect: Expect1;
  family: ScenarioFamily;
  id: Id19;
  rules: Rules2;
  steps: Steps2;
}
export interface Cart1 {
  [k: string]: JsonValue;
}
export interface Expect1 {
  [k: string]: JsonValue;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ShopPackV1".
 */
export interface ShopPackV1 {
  answer_key: AnswerKey;
  buyer_script: BuyerScript;
  env_needed: EnvNeeded;
  framework: Framework2;
  health_url: HealthUrl;
  language: Language1;
  licence: Licence;
  name: Name1;
  port: Port;
  scenarios_supported: ScenariosSupported;
  shop_id: ShopId5;
  source: ShopSource;
  start: Start;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AnswerKey".
 */
export interface AnswerKey {
  money_flow: MoneyFlow;
  touchpoints: Touchpoints1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ShopSource".
 */
export interface ShopSource {
  commit: Commit1;
  repo: Repo2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ComposeStart".
 */
export interface ComposeStart {
  compose_file: ComposeFile;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CommandStart".
 */
export interface CommandStart {
  command: Command;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StageChangeV1".
 */
export interface StageChangeV1 {
  actor: StageActor;
  attempt: Attempt1;
  evidence_refs: EvidenceRefs4;
  from_stage: StageName | null;
  graft_id: GraftId17;
  reason: Reason2;
  to_stage: StageName;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StageActor".
 */
export interface StageActor {
  kind: ProducerKind;
  name: Name2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SwitchConfigV1".
 */
export interface SwitchConfigV1 {
  expires_at: ExpiresAt;
  graft_id: GraftId18;
  origin_rules: OriginRules;
  signature: Signature4;
  stage_pct: StagePct1;
  version: Version1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TargetPlanV1".
 */
export interface TargetPlanV1 {
  deltas?: Deltas;
  handoff: Handoff;
  items: Items;
  order: Order;
  origin_rules: OriginRules1;
  path: PlanPath;
  target_experience: TargetExperience;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "IntentDelta".
 */
export interface IntentDelta {
  description: Description;
  id: Id20;
  mapping_id: MappingId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PlanItem".
 */
export interface PlanItem {
  delta_ids: DeltaIds;
  mapping_id: MappingId1;
  paypal_only: PaypalOnly1;
  target_op: TargetOp;
  touchpoint: Touchpoint1;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TriangleRequestV1".
 */
export interface TriangleRequestV1 {
  created_at: CreatedAt10;
  graft_id: GraftId19;
  id: Id21;
  mutant_ids: MutantIds1;
  producer: Producer;
  reason: Reason3;
  rule_id: RuleId;
  scenario_ids: ScenarioIds1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "VerdictV1".
 */
export interface VerdictV1 {
  deltas_applied: DeltasApplied;
  grade: Grade;
  noise_masked: NoiseMasked;
  parity_diff: ParityDiff;
  rule_hits: RuleHits;
  scenario_id: ScenarioId2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RuleHit".
 */
export interface RuleHit {
  evidence: Evidence;
  rule: Rule3;
  side: Side;
}
