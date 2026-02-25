from fastapi import FastAPI
from fastapi.responses import HTMLResponse

ui_app = FastAPI(title="Procurement Webapp UI", version="2.1.0")


@ui_app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _HTML


_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Hurricane Fence - Procurement Platform</title>
<style>
:root{
  --bg:#040707;--sidebar:#0a0e12;--surface:#0f1519;--surface2:#151c22;
  --border:#1e2a32;--text:#fcfdfd;--muted:#8a9299;
  --blue:#1090be;--cyan:#17dcef;--red:#cf152d;--white:#fcfdfd;
  --gray:#545454;--green:#22c55e;--amber:#f59e0b;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);display:flex;min-height:100vh}
button{cursor:pointer;font-family:inherit}
input,select,textarea{font-family:inherit}

/* Sidebar */
.sidebar{width:220px;background:var(--sidebar);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0;position:fixed;top:0;left:0;bottom:0;z-index:100}
.sidebar-brand{padding:16px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px}
.sidebar-brand img{height:32px;width:auto}
.sidebar-brand .brand-text{font-size:11px;font-weight:700;color:var(--cyan);text-transform:uppercase;letter-spacing:.08em;line-height:1.3}
.sidebar-brand .brand-sub{font-size:9px;color:var(--muted);font-weight:500;letter-spacing:.04em}
.sidebar-nav{flex:1;padding:8px}
.nav-section{font-size:9px;color:var(--gray);text-transform:uppercase;letter-spacing:.1em;padding:12px 12px 4px;font-weight:700}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:6px;font-size:12px;font-weight:500;color:var(--muted);cursor:pointer;transition:all .15s;border:none;background:none;width:100%;text-align:left}
.nav-item:hover{background:var(--surface2);color:var(--text)}
.nav-item.active{background:var(--blue);color:#fff}
.nav-item .icon{width:16px;text-align:center;font-size:13px}
.nav-item .badge{margin-left:auto;background:var(--red);color:#fff;font-size:9px;padding:2px 6px;border-radius:99px;font-weight:700}
.sidebar-footer{padding:10px 14px;border-top:1px solid var(--border)}
.sidebar-footer select{width:100%;background:var(--surface);border:1px solid var(--border);color:var(--text);padding:7px;border-radius:6px;font-size:11px}
.sidebar-footer label{font-size:9px;color:var(--gray);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:3px}

/* Main */
.main{margin-left:220px;flex:1;display:flex;flex-direction:column;min-height:100vh}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:12px 20px;border-bottom:1px solid var(--border);background:var(--sidebar)}
.topbar h2{font-size:16px;font-weight:600}
.topbar-actions{display:flex;gap:6px}
.btn{padding:7px 14px;border-radius:6px;font-size:11px;font-weight:600;border:1px solid var(--border);background:var(--surface);color:var(--text);transition:all .15s}
.btn:hover{background:var(--surface2)}
.btn-primary{background:var(--blue);border-color:var(--blue);color:#fff}
.btn-primary:hover{opacity:.9}
.btn-sm{padding:4px 9px;font-size:10px}
.btn-green{background:var(--green);border-color:var(--green);color:#fff}
.btn-amber{background:var(--amber);border-color:var(--amber);color:#000}
.btn-red{background:var(--red);border-color:var(--red);color:#fff}
.btn-cyan{background:var(--cyan);border-color:var(--cyan);color:#000}
.content{flex:1;padding:20px;overflow-y:auto}

/* KPIs */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:10px;margin-bottom:16px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px}
.kpi-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}
.kpi-value{font-size:24px;font-weight:700}
.kpi-sub{font-size:10px;color:var(--muted);margin-top:3px}

/* Process Groups */
.process-group{margin-bottom:16px;background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.process-header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--border);cursor:pointer;user-select:none}
.process-header:hover{background:var(--surface2)}
.process-title{display:flex;align-items:center;gap:10px}
.process-num{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;flex-shrink:0}
.process-name{font-size:13px;font-weight:700}
.process-desc{font-size:10px;color:var(--muted);margin-left:36px;margin-top:2px}
.process-stats{display:flex;gap:12px;font-size:11px;color:var(--muted)}
.process-stats span{display:flex;align-items:center;gap:4px}
.process-body{display:flex;gap:8px;padding:10px;overflow-x:auto;align-items:flex-start}
.process-body.collapsed{display:none}

/* Decision Gate */
.decision-gate{display:flex;align-items:center;justify-content:center;padding:6px 16px;background:var(--surface2);border-top:1px solid var(--border);font-size:10px;color:var(--cyan);gap:6px}
.decision-gate .diamond{width:12px;height:12px;background:var(--cyan);transform:rotate(45deg);border-radius:2px;flex-shrink:0;opacity:.6}

/* Lanes inside process groups */
.lane{min-width:210px;max-width:230px;flex-shrink:0;background:var(--surface2);border:1px solid var(--border);border-radius:8px;display:flex;flex-direction:column;max-height:380px}
.lane-header{padding:8px 10px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.lane-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.lane-count{font-size:10px;background:var(--bg);padding:2px 7px;border-radius:99px;color:var(--text);font-weight:600}
.lane-body{padding:5px;overflow-y:auto;flex:1;display:flex;flex-direction:column;gap:5px}

/* Cards */
.card{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:9px;cursor:pointer;transition:border-color .15s}
.card:hover{border-color:var(--blue)}
.card-job{font-size:12px;font-weight:700;color:var(--cyan);margin-bottom:3px}
.card-vendor{font-size:10px;color:var(--muted);margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-row{display:flex;justify-content:space-between;align-items:center;font-size:10px}
.card-amount{font-weight:600;color:var(--text)}
.pill{display:inline-block;font-size:9px;padding:2px 7px;border-radius:99px;font-weight:600}
.pill-high{background:rgba(207,21,45,.15);color:var(--red)}
.pill-normal{background:rgba(16,144,190,.12);color:var(--blue)}
.pill-human{background:rgba(245,158,11,.15);color:var(--amber)}
.pill-auto{background:rgba(34,197,94,.12);color:var(--green)}

/* Tables */
.data-table{width:100%;border-collapse:collapse;font-size:11px}
.data-table th{text-align:left;padding:9px 10px;background:var(--surface2);color:var(--muted);font-weight:600;text-transform:uppercase;font-size:9px;letter-spacing:.04em;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:1}
.data-table td{padding:9px 10px;border-bottom:1px solid var(--border);vertical-align:middle}
.data-table tr:hover td{background:rgba(16,144,190,.04)}
.table-wrap{background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:auto;max-height:calc(100vh - 230px)}

/* Detail panel */
.detail-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);z-index:200;display:none;align-items:flex-start;justify-content:flex-end}
.detail-overlay.open{display:flex}
.detail-panel{width:440px;max-width:90vw;background:var(--sidebar);border-left:1px solid var(--border);height:100vh;overflow-y:auto;padding:20px;animation:slideIn .2s ease}
@keyframes slideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}
.detail-panel h3{font-size:15px;margin-bottom:14px;color:var(--cyan)}
.detail-field{margin-bottom:10px}
.detail-field label{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;display:block;margin-bottom:3px}
.detail-field .val{font-size:13px}
.detail-actions{display:flex;flex-wrap:wrap;gap:6px;margin-top:16px;padding-top:14px;border-top:1px solid var(--border)}

/* Activity */
.activity-item{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid var(--border)}
.activity-dot{width:7px;height:7px;border-radius:50%;margin-top:5px;flex-shrink:0}
.activity-dot.auto{background:var(--green)}
.activity-dot.human{background:var(--amber)}
.activity-text{font-size:12px;flex:1}
.activity-meta{font-size:10px;color:var(--muted);margin-top:2px}

/* Pages */
.page{display:none}
.page.active{display:block}
.status-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px}
.status-dot.green{background:var(--green)}
.status-dot.amber{background:var(--amber)}
.status-dot.red{background:var(--red)}
.status-dot.blue{background:var(--blue)}
.empty-state{text-align:center;padding:30px 16px;color:var(--muted);font-size:12px}

/* Intake Form */
.intake-form-wrap{background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:hidden}
.intake-form-header{display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid var(--border);background:var(--surface2)}
.intake-form-icon{font-size:18px}
.intake-form-body{padding:14px;display:flex;flex-direction:column;gap:10px}
.form-row{display:flex;flex-direction:column;gap:3px}
.form-row label{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.form-row input,.form-row select,.form-row textarea{background:var(--bg);border:1px solid var(--border);color:var(--text);padding:8px 10px;border-radius:6px;font-size:12px;transition:border-color .15s}
.form-row input:focus,.form-row select:focus,.form-row textarea:focus{outline:none;border-color:var(--blue)}
.form-row textarea{resize:vertical}
.form-row-2col{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.form-divider{height:1px;background:var(--border);margin:2px 0}
.form-actions{display:flex;gap:8px;margin-top:4px}
.intake-form-footer{display:flex;align-items:flex-start;gap:8px;padding:10px 14px;border-top:1px solid var(--border);background:var(--surface2)}
.intake-form-footer-icon{font-size:14px;margin-top:1px}

@media(max-width:900px){
  .sidebar{width:56px}
  .sidebar-brand img{height:24px}
  .sidebar-brand .brand-text,.sidebar-brand .brand-sub,.nav-section,.nav-item span:not(.icon),.sidebar-footer label{display:none}
  .main{margin-left:56px}
  .nav-item{justify-content:center;padding:10px}
}

/* Modern UX enhancements */
:root{
  --bg:#060a12;--sidebar:#0b1424;--surface:#101b2d;--surface2:#162338;--surface3:#1c2d47;
  --border:#263b59;--text:#eef4ff;--muted:#9fb1cd;--blue:#4f8cff;--cyan:#4cc9f0;
  --red:#ff5d73;--gray:#6f86a6;--green:#34d399;--amber:#fbbf24;
}
body{background:radial-gradient(circle at 10% -10%,#17335a 0,#060a12 40%),var(--bg);color:var(--text)}
.sidebar{background:linear-gradient(180deg,#0b1424 0%,#09101d 100%);box-shadow:0 0 0 1px rgba(255,255,255,.02),8px 0 30px rgba(0,0,0,.25)}
.nav-item{border:1px solid transparent}
.nav-item:hover{background:var(--surface3);border-color:var(--border)}
.nav-item.active{background:linear-gradient(135deg,#4f8cff,#3b74ec)}
.main{background:transparent}
.topbar{position:sticky;top:0;z-index:20;background:rgba(9,16,29,.88);backdrop-filter:blur(10px)}
.content{padding:22px 24px 28px}
.hero-card{padding:16px 18px;border:1px solid var(--border);background:linear-gradient(130deg,rgba(79,140,255,.18),rgba(76,201,240,.06) 45%,rgba(16,27,45,.8));border-radius:14px;margin-bottom:14px;display:flex;justify-content:space-between;gap:12px;align-items:center}
.hero-title{font-size:18px;font-weight:700;margin-bottom:4px}
.hero-sub{font-size:12px;color:var(--muted)}
.hero-meta{display:flex;gap:10px;flex-wrap:wrap}
.hero-chip{font-size:11px;padding:5px 10px;border-radius:999px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12)}
.kpi{background:linear-gradient(180deg,rgba(21,35,56,.95),rgba(12,21,35,.95));border-color:#2c456b;border-radius:12px}
.kpi-value{letter-spacing:-.02em}
.dashboard-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:14px}
.workflow-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin:14px 0 16px}
.workflow-node{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px;position:relative}
.workflow-node .name{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.workflow-node .count{font-size:20px;font-weight:700;margin-top:4px}
.workflow-node .meta{font-size:10px;color:var(--muted)}
.board-toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;padding:10px;border:1px solid var(--border);background:var(--surface);border-radius:12px}
.board-toolbar input,.board-toolbar select{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:7px 10px;border-radius:8px;font-size:12px}
.board-toolbar .chip-btn{padding:7px 10px;border-radius:8px;border:1px solid var(--border);background:var(--surface2);color:var(--muted);font-size:11px;font-weight:600}
.board-toolbar .chip-btn.active{background:rgba(79,140,255,.25);color:var(--text);border-color:#3d67a5}
.process-group{border-radius:14px;border-color:#2a4366;background:linear-gradient(180deg,rgba(15,27,44,.95),rgba(11,20,33,.95));margin-bottom:14px}
.process-header{padding:14px 16px}
.lane{background:rgba(22,35,56,.8);border-color:#304a70;border-radius:10px}
.card{border-radius:10px;border:1px solid #2e4970;background:#111f33;box-shadow:0 6px 14px rgba(0,0,0,.2)}
.card:hover{transform:translateY(-1px);border-color:#4a75b6}
.table-wrap{background:var(--surface);border-radius:12px;border:1px solid var(--border)}
.data-table th{background:#10203a}
.detail-panel{border:1px solid var(--border);border-radius:14px}

.board-layout{display:grid;grid-template-columns:300px 1fr;gap:12px;align-items:start}
.flow-panel{position:sticky;top:74px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px}
.flow-title{font-size:12px;font-weight:700;margin-bottom:4px}
.flow-sub{font-size:11px;color:var(--muted);margin-bottom:10px}
.flow-step{display:flex;gap:8px;padding:8px;border:1px solid var(--border);background:var(--surface2);border-radius:10px;margin-bottom:8px;cursor:pointer;transition:all .15s}
.flow-step:hover{border-color:#4974b7}
.flow-step.active{border-color:var(--cyan);background:rgba(76,201,240,.12)}
.flow-step-num{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;background:#22344f;color:var(--text);flex-shrink:0}
.flow-step-meta{font-size:10px;color:var(--muted);margin-top:2px}
.flow-step-count{margin-left:auto;font-size:10px;background:#0d1727;border:1px solid var(--border);padding:2px 7px;border-radius:99px;height:fit-content}
.quick-queue{margin-top:10px;padding-top:10px;border-top:1px solid var(--border)}
.queue-item{display:flex;align-items:center;justify-content:space-between;font-size:11px;padding:6px 0;border-bottom:1px dashed rgba(159,177,205,.25)}
.queue-item:last-child{border-bottom:none}
@media(max-width:1200px){.board-layout{grid-template-columns:1fr}.flow-panel{position:static}}

@media(max-width:1200px){.dashboard-grid{grid-template-columns:1fr}.hero-card{flex-direction:column;align-items:flex-start}}

</style>
</head>
<body>

<aside class="sidebar">
  <div class="sidebar-brand">
    <img src="/static/logo.png" alt="Hurricane Fence"/>
    <div>
      <div class="brand-text">Procurement</div>
      <div class="brand-sub">Workflow Platform</div>
    </div>
  </div>
  <nav class="sidebar-nav">
    <div class="nav-section">Overview</div>
    <button class="nav-item active" data-page="dashboard">
      <span class="icon">&#9632;</span><span>Dashboard</span>
    </button>
    <div class="nav-section">Workflow</div>
    <button class="nav-item" data-page="board">
      <span class="icon">&#9776;</span><span>Job Board</span>
    </button>
    <button class="nav-item" data-page="approvals">
      <span class="icon">&#10003;</span><span>Approvals</span>
      <span class="badge" id="approvalBadge" style="display:none">0</span>
    </button>
    <div class="nav-section">Data</div>
    <button class="nav-item" data-page="vendors">
      <span class="icon">&#9733;</span><span>Vendors</span>
    </button>
    <button class="nav-item" data-page="activity">
      <span class="icon">&#8635;</span><span>Activity Log</span>
    </button>
    <div class="nav-section">Intake</div>
    <button class="nav-item" data-page="intake">
      <span class="icon">&#9993;</span><span>Email Intake</span>
    </button>
  </nav>
  <div class="sidebar-footer">
    <label>Acting As</label>
    <select id="userEmail">
      <option value="buyer@hurricanefence.com">Buyer</option>
      <option value="approver@hurricanefence.com">Approver</option>
      <option value="admin@hurricanefence.com">Admin</option>
    </select>
  </div>
</aside>

<div class="main">
  <div class="topbar">
    <h2 id="pageTitle">Dashboard</h2>
    <div class="topbar-actions">
      <button class="btn" onclick="refreshAll()">Refresh</button>
    </div>
  </div>
  <div class="content">

    <!-- DASHBOARD -->
    <div class="page active" id="page-dashboard">
      <div class="hero-card">
        <div>
          <div class="hero-title">Purchasing Command Center</div>
          <div class="hero-sub">Track every procurement milestone from intake through fulfillment without losing your current workflow logic.</div>
        </div>
        <div class="hero-meta">
          <span class="hero-chip" id="heroRefresh">Auto-refresh: 30s</span>
          <span class="hero-chip" id="heroApprovals">Pending approvals: 0</span>
          <span class="hero-chip" id="heroHighPriority">High priority: 0</span>
        </div>
      </div>
      <div class="kpi-row" id="kpiRow"></div>
      <div class="workflow-strip" id="workflowStrip"></div>
      <div class="dashboard-grid">
        <div>
          <h3 style="font-size:13px;margin-bottom:8px;color:var(--cyan)">Process Overview</h3>
          <div class="table-wrap" style="max-height:340px">
            <table class="data-table"><thead><tr><th>Process</th><th>Stage</th><th>Count</th></tr></thead><tbody id="stageTable"></tbody></table>
          </div>
        </div>
        <div>
          <h3 style="font-size:13px;margin-bottom:8px;color:var(--cyan)">Recent Activity</h3>
          <div id="dashActivity" style="max-height:340px;overflow-y:auto"></div>
        </div>
      </div>
    </div>

    <!-- JOB BOARD -->
    <div class="page" id="page-board">
      <div class="board-toolbar">
        <input type="search" id="boardSearch" placeholder="Search by job #, vendor, PO" oninput="renderBoard()"/>
        <select id="boardPriority" onchange="renderBoard()">
          <option value="all">All priorities</option>
          <option value="high">High priority only</option>
          <option value="normal">Normal priority only</option>
        </select>
        <button class="chip-btn" id="boardNeedsAction" onclick="toggleNeedsActionFilter()">Needs Human Action</button>
        <button class="chip-btn" id="boardClearFilters" onclick="clearBoardFilters()">Clear Filters</button>
      </div>
      <div class="board-layout">
        <aside class="flow-panel">
          <div class="flow-title">Workflow Navigator</div>
          <div class="flow-sub">Focus on one lifecycle group at a time while keeping the full process model intact.</div>
          <div id="flowSteps"></div>
          <div class="quick-queue">
            <div class="flow-title" style="font-size:11px">Needs attention next</div>
            <div id="attentionQueue"></div>
          </div>
        </aside>
        <div id="jobBoard"></div>
      </div>
    </div>

    <!-- APPROVALS -->
    <div class="page" id="page-approvals">
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Task</th><th>Job</th><th>Stage</th><th>Priority</th><th>Reason</th><th>Amount</th><th>Action</th></tr></thead>
          <tbody id="approvalRows"></tbody>
        </table>
      </div>
    </div>

    <!-- VENDORS -->
    <div class="page" id="page-vendors">
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Vendor</th><th>Code</th><th>Class</th><th>Status</th></tr></thead>
          <tbody id="vendorRows"></tbody>
        </table>
      </div>
    </div>

    <!-- ACTIVITY -->
    <div class="page" id="page-activity">
      <div id="activityList"></div>
    </div>

    <!-- INTAKE -->
    <div class="page" id="page-intake">
      <div style="display:grid;grid-template-columns:380px 1fr;gap:16px;align-items:start">

        <div class="intake-form-wrap">
          <div class="intake-form-header">
            <span class="intake-form-icon">&#9993;</span>
            <div>
              <div style="font-size:13px;font-weight:700">New Job Intake</div>
              <div style="font-size:10px;color:var(--muted)">Submit manually or will auto-populate from forwarded email</div>
            </div>
          </div>
          <div class="intake-form-body">
            <div class="form-row">
              <label>Source</label>
              <select id="intakeSource">
                <option value="manual">Manual Entry</option>
                <option value="email_forward">Email Forward</option>
                <option value="email_cc">Email CC</option>
              </select>
            </div>
            <div class="form-row">
              <label>Submitted By (PMA Email)</label>
              <input type="email" id="intakeSubmittedBy" placeholder="pma@hurricanefence.com"/>
            </div>
            <div class="form-row">
              <label>Subject / Description</label>
              <input type="text" id="intakeSubject" placeholder="Budget for Job 2241028 - NC"/>
            </div>
            <div class="form-divider"></div>
            <div class="form-row-2col">
              <div class="form-row">
                <label>Job Number</label>
                <input type="text" id="intakeJobNumber" placeholder="2241028"/>
              </div>
              <div class="form-row">
                <label>Location</label>
                <input type="text" id="intakeLocation" placeholder="North Carolina"/>
              </div>
            </div>
            <div class="form-row-2col">
              <div class="form-row">
                <label>Budget Amount</label>
                <input type="number" id="intakeBudget" placeholder="0.00" step="0.01"/>
              </div>
              <div class="form-row">
                <label>Priority</label>
                <select id="intakePriority">
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            <div class="form-row-2col">
              <div class="form-row">
                <label>Vendor (if known)</label>
                <input type="text" id="intakeVendor" placeholder="Optional"/>
              </div>
              <div class="form-row">
                <label>PO Number (if exists)</label>
                <input type="text" id="intakePO" placeholder="Optional"/>
              </div>
            </div>
            <div class="form-row">
              <label>Notes</label>
              <textarea id="intakeNotes" rows="3" placeholder="Additional context, forwarded email body, etc."></textarea>
            </div>
            <div class="form-actions">
              <button class="btn btn-primary" onclick="submitIntake()" style="flex:1">Submit to Job Board</button>
              <button class="btn" onclick="clearIntakeForm()">Clear</button>
            </div>
          </div>
          <div class="intake-form-footer">
            <span class="intake-form-footer-icon">&#128268;</span>
            <div>
              <div style="font-size:10px;font-weight:600;color:var(--cyan)">Future: Auto-intake via Email</div>
              <div style="font-size:9px;color:var(--muted)">PMAs will CC or forward to a dedicated inbox. The system will parse job number, budget, and vendor automatically.</div>
            </div>
          </div>
        </div>

        <div>
          <h3 style="font-size:13px;margin-bottom:8px;color:var(--cyan)">Recent Intake Submissions</h3>
          <div class="table-wrap" style="max-height:calc(100vh - 200px)">
            <table class="data-table">
              <thead><tr><th>ID</th><th>Job #</th><th>Submitted By</th><th>Vendor</th><th>Amount</th><th>Stage</th><th>Priority</th><th>Source</th><th>Date</th></tr></thead>
              <tbody id="intakeRows"></tbody>
            </table>
          </div>
        </div>

      </div>
    </div>

  </div>
</div>

<div class="detail-overlay" id="detailOverlay" onclick="if(event.target===this)closeDetail()">
  <div class="detail-panel" id="detailPanel"></div>
</div>

<script>
const API="/api";

const PROCESS_GROUPS=[
  {
    id:"initiation",
    name:"Job Initiation & Budget",
    color:"var(--blue)",
    desc:"Job enters system, budget is reviewed and approved by Project Manager",
    decision:"Budget Approved? \u2192 Assign to Purchaser",
    stages:[
      ["job_setup","Job Setup"],
      ["budget_review","Budget Review"],
    ]
  },
  {
    id:"assignment",
    name:"Assignment & Material Check",
    color:"var(--cyan)",
    desc:"Purchaser assigned, check if material is stocked or can be pulled from extra inventory",
    decision:"Material In Stock? \u2192 Yes: Pull from Yard  |  No: Proceed to Procurement",
    stages:[
      ["task_assignment","Task Assignment"],
      ["material_check","Material Check"],
    ]
  },
  {
    id:"procurement",
    name:"Procurement & Ordering",
    color:"var(--amber)",
    desc:"Validate pricing, coordinate with vendors on price/delivery/location, place order",
    decision:"Order Placed? \u2192 Await vendor confirmation and delivery",
    stages:[
      ["pricing_validation","Pricing / PO"],
      ["vendor_coordination","Vendor Coordination"],
      ["order_placement","Order Placement"],
    ]
  },
  {
    id:"fulfillment",
    name:"Fulfillment & Closeout",
    color:"var(--green)",
    desc:"Confirm order, generate yard pull, receive material, verify completion",
    decision:"All Material Present? \u2192 Yes: Complete  |  No: Reorder missing items",
    stages:[
      ["order_confirmation","Order Confirmation"],
      ["yard_pull","Yard Pull"],
      ["material_receiving","Material Receiving"],
      ["completion_check","Completion Check"],
      ["completed","Completed"],
    ]
  }
];

const ALL_STAGES=PROCESS_GROUPS.flatMap(g=>g.stages);
const STAGE_LABELS=Object.fromEntries(ALL_STAGES);

let STATE={tasks:[],approvals:[],vendors:[],actions:[],summary:{}};
let collapsedGroups={};
let boardNeedsActionOnly=false;
let focusedGroup="all";

function headers(){return{"X-User-Email":document.getElementById("userEmail").value,"Content-Type":"application/json"}}
function money(v){return"$"+Number(v||0).toLocaleString(undefined,{maximumFractionDigits:0})}

async function api(path,opts={}){
  const res=await fetch(API+path,{headers:headers(),...opts});
  if(!res.ok){
    if(opts.allow403&&res.status===403)return null;
    console.warn(path,res.status);
    return null;
  }
  return res.json();
}

document.querySelectorAll(".nav-item").forEach(btn=>{
  btn.addEventListener("click",()=>{
    document.querySelectorAll(".nav-item").forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    const pg=btn.dataset.page;
    document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
    document.getElementById("page-"+pg).classList.add("active");
    document.getElementById("pageTitle").textContent=btn.querySelector("span:last-child").textContent;
  });
});

async function loadAll(){
  const [summary,tasks,approvals,vendors,actions]=await Promise.all([
    api("/dashboard/summary"),
    api("/tasks?limit=500"),
    api("/approvals/financial?limit=200",{allow403:true}),
    api("/vendors?limit=500"),
    api("/workflow/actions/recent?limit=100"),
  ]);
  STATE.summary=summary||{};
  STATE.tasks=tasks||[];
  STATE.approvals=approvals||[];
  STATE.vendors=vendors||[];
  STATE.actions=actions||[];
  renderDashboard();
  renderBoard();
  renderApprovals();
  renderVendors();
  renderActivity();
}

// ---- Dashboard ----
function renderDashboard(){
  const s=STATE.summary;
  const kpis=[
    {label:"Open Jobs",value:s.open_tasks||0,color:"var(--blue)"},
    {label:"Awaiting Approval",value:s.financial_approvals_pending||0,color:"var(--amber)"},
    {label:"Invoice Exceptions",value:s.open_invoice_exceptions||0,color:"var(--red)"},
    {label:"Pending Confirmations",value:s.pending_order_confirmations||0,color:"var(--cyan)"},
    {label:"High Priority",value:s.open_high_priority_tasks||0,color:"var(--red)"},
    {label:"Tracked PO Spend",value:money(s.tracked_po_spend),color:"var(--green)"},
  ];
  document.getElementById("kpiRow").innerHTML=kpis.map(k=>`
    <div class="kpi">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-value" style="color:${k.color}">${k.value}</div>
    </div>`).join("");

  const stageCounts={};
  STATE.tasks.forEach(t=>{const st=t.workflow_stage||"unknown";stageCounts[st]=(stageCounts[st]||0)+1});

  let tableHtml="";
  PROCESS_GROUPS.forEach(g=>{
    g.stages.forEach(([key,label],i)=>{
      const n=stageCounts[key]||0;
      tableHtml+=`<tr>
        <td>${i===0?`<span style="color:${g.color};font-weight:700">${g.name}</span>`:""}</td>
        <td>${label}</td>
        <td style="font-weight:600">${n}</td>
      </tr>`;
    });
  });
  document.getElementById("stageTable").innerHTML=tableHtml||"<tr><td colspan=3 class='empty-state'>No data</td></tr>";

  document.getElementById("heroApprovals").textContent=`Pending approvals: ${s.financial_approvals_pending||0}`;
  document.getElementById("heroHighPriority").textContent=`High priority: ${s.open_high_priority_tasks||0}`;

  const workflowNodes=ALL_STAGES.map(([key,label])=>`<div class="workflow-node"><div class="name">${label}</div><div class="count">${stageCounts[key]||0}</div><div class="meta">${(stageCounts[key]||0)===1?"task":"tasks"}</div></div>`).join("");
  document.getElementById("workflowStrip").innerHTML=workflowNodes;

  document.getElementById("dashActivity").innerHTML=(STATE.actions||[]).slice(0,12).map(a=>`
    <div class="activity-item">
      <div class="activity-dot ${a.action_mode}"></div>
      <div>
        <div class="activity-text"><strong>${a.action_type}</strong> on Task ${a.task_id||""}</div>
        <div class="activity-meta">${a.actor_email||"system"} &middot; ${a.action_mode}</div>
      </div>
    </div>`).join("")||"<div class='empty-state'>No recent activity</div>";
}

// ---- Job Board (Process Groups) ----
function renderBoard(){
  const byStage={};
  const search=(document.getElementById("boardSearch")?.value||"").toLowerCase().trim();
  const priority=document.getElementById("boardPriority")?.value||"all";
  ALL_STAGES.forEach(([k])=>byStage[k]=[]);
  STATE.tasks.forEach(t=>{
    const d=t.details||{};
    const text=[t.job_number,d.vendor,d.po_number].filter(Boolean).join(" ").toLowerCase();
    if(search && !text.includes(search)) return;
    if(priority!=="all" && t.priority!==priority) return;
    if(boardNeedsActionOnly && !t.human_required) return;
    const st=t.workflow_stage||"job_setup";
    if(!byStage[st])byStage[st]=[];
    byStage[st].push(t);
  });

  const groupCounts=PROCESS_GROUPS.map(g=>({
    id:g.id,
    count:g.stages.reduce((sum,[stage])=>sum+(byStage[stage]||[]).length,0),
    human:g.stages.reduce((sum,[stage])=>sum+(byStage[stage]||[]).filter(t=>t.human_required).length,0),
  }));
  renderFlowNavigator(groupCounts,byStage);

  document.getElementById("jobBoard").innerHTML=PROCESS_GROUPS.filter(g=>focusedGroup==="all"||g.id===focusedGroup).map((g,gi)=>{
    const groupTotal=g.stages.reduce((s,[k])=>s+(byStage[k]||[]).length,0);
    const humanCount=g.stages.reduce((s,[k])=>s+(byStage[k]||[]).filter(t=>t.human_required).length,0);
    const isCollapsed=collapsedGroups[g.id];

    const lanes=g.stages.map(([key,label])=>{
      const items=byStage[key]||[];
      const cards=items.slice(0,25).map(t=>renderCard(t)).join("");
      const overflow=items.length>25?`<div style="padding:5px;font-size:10px;color:var(--muted);text-align:center">+${items.length-25} more</div>`:"";
      return`<div class="lane">
        <div class="lane-header">
          <span class="lane-title">${label}</span>
          <span class="lane-count">${items.length}</span>
        </div>
        <div class="lane-body">${cards||"<div class='empty-state'>Empty</div>"}${overflow}</div>
      </div>`;
    }).join("");

    return`<div class="process-group">
      <div class="process-header" onclick="toggleGroup('${g.id}')">
        <div>
          <div class="process-title">
            <div class="process-num" style="background:${g.color}">${PROCESS_GROUPS.findIndex(pg=>pg.id===g.id)+1}</div>
            <span class="process-name">${g.name}</span>
          </div>
          <div class="process-desc">${g.desc}</div>
        </div>
        <div class="process-stats">
          <span><strong style="color:var(--text)">${groupTotal}</strong> jobs</span>
          ${humanCount?`<span><strong style="color:var(--amber)">${humanCount}</strong> need action</span>`:""}
          <span style="font-size:14px">${isCollapsed?"\u25B6":"\u25BC"}</span>
        </div>
      </div>
      <div class="process-body${isCollapsed?" collapsed":""}">${lanes}</div>
      <div class="decision-gate">
        <div class="diamond"></div>
        <span>${g.decision}</span>
      </div>
    </div>`;
  }).join("");
}

function renderCard(t){
  const d=t.details||{};
  const pri=t.priority==="high"?"pill-high":"pill-normal";
  const mode=t.human_required?"pill-human":"pill-auto";
  return`<div class="card" onclick="openDetail(${t.id})">
    <div class="card-job">${t.job_number||"No Job #"}</div>
    <div class="card-vendor">${d.vendor||"Unknown vendor"}</div>
    <div class="card-row">
      <span class="pill ${pri}">${t.priority}</span>
      <span class="card-amount">${d.total!=null?money(d.total):""}</span>
    </div>
    ${t.human_required?`<div class="card-row" style="margin-top:3px"><span class="pill pill-human">Needs Approval</span></div>`:""}
  </div>`;
}



function renderFlowNavigator(groupCounts,byStage){
  const steps=PROCESS_GROUPS.map((g,idx)=>{
    const count=groupCounts.find(x=>x.id===g.id)?.count||0;
    const human=groupCounts.find(x=>x.id===g.id)?.human||0;
    const active=focusedGroup===g.id;
    return `<div class="flow-step ${active?"active":""}" onclick="setFocusedGroup('${g.id}')">
      <div class="flow-step-num">${idx+1}</div>
      <div>
        <div style="font-size:11px;font-weight:600">${g.name}</div>
        <div class="flow-step-meta">${human?`${human} require action · `:""}${g.decision}</div>
      </div>
      <div class="flow-step-count">${count}</div>
    </div>`;
  }).join("");
  const allCount=groupCounts.reduce((sum,g)=>sum+g.count,0);
  document.getElementById("flowSteps").innerHTML=`<div class="flow-step ${focusedGroup==="all"?"active":""}" onclick="setFocusedGroup('all')">
      <div class="flow-step-num">*</div>
      <div><div style="font-size:11px;font-weight:600">All workflow groups</div><div class="flow-step-meta">Full end-to-end purchasing board</div></div>
      <div class="flow-step-count">${allCount}</div>
    </div>`+steps;

  const attention=[...STATE.tasks]
    .filter(t=>t.human_required || t.priority==="high")
    .sort((a,b)=>Number(b.human_required)-Number(a.human_required))
    .slice(0,6)
    .map(t=>`<div class="queue-item"><span>${t.job_number||"No job #"}</span><span>${t.human_required?"Approval":"High"}</span></div>`)
    .join("");
  document.getElementById("attentionQueue").innerHTML=attention||"<div class='empty-state' style='padding:6px 0'>No urgent work items.</div>";
}

function setFocusedGroup(groupId){
  focusedGroup=groupId;
  renderBoard();
}

function clearBoardFilters(){
  const search=document.getElementById("boardSearch");
  const priority=document.getElementById("boardPriority");
  if(search) search.value="";
  if(priority) priority.value="all";
  boardNeedsActionOnly=false;
  focusedGroup="all";
  const btn=document.getElementById("boardNeedsAction");
  if(btn) btn.classList.remove("active");
  renderBoard();
}

function toggleNeedsActionFilter(){
  boardNeedsActionOnly=!boardNeedsActionOnly;
  const btn=document.getElementById("boardNeedsAction");
  if(btn) btn.classList.toggle("active",boardNeedsActionOnly);
  renderBoard();
}

function toggleGroup(id){
  collapsedGroups[id]=!collapsedGroups[id];
  renderBoard();
}

// ---- Detail Panel ----
function openDetail(taskId){
  const t=STATE.tasks.find(x=>x.id===taskId);
  if(!t)return;
  const d=t.details||{};
  const stage=STAGE_LABELS[t.workflow_stage]||t.workflow_stage;
  const group=PROCESS_GROUPS.find(g=>g.stages.some(([k])=>k===t.workflow_stage));
  const actions=getAvailableActions(t);

  document.getElementById("detailPanel").innerHTML=`
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h3>Task #${t.id}</h3>
      <button class="btn btn-sm" onclick="closeDetail()">Close</button>
    </div>
    ${group?`<div style="margin-bottom:14px;padding:8px 10px;border-radius:6px;background:var(--surface2);font-size:11px;color:var(--muted)">
      <strong style="color:${group.color}">${group.name}</strong> &middot; ${stage}
    </div>`:""}
    <div class="detail-field"><label>Job Number</label><div class="val">${t.job_number||"N/A"}</div></div>
    <div class="detail-field"><label>Status</label><div class="val"><span class="status-dot ${t.status==='completed'?'green':t.human_required?'amber':'blue'}"></span>${t.status}</div></div>
    <div class="detail-field"><label>Priority</label><div class="val">${t.priority}</div></div>
    <div class="detail-field"><label>Vendor</label><div class="val">${d.vendor||"N/A"}</div></div>
    <div class="detail-field"><label>PO Number</label><div class="val">${d.po_number||"N/A"}</div></div>
    <div class="detail-field"><label>Amount</label><div class="val">${d.total!=null?money(d.total):"N/A"}</div></div>
    <div class="detail-field"><label>Requires Human Action</label><div class="val">${t.human_required?"Yes":"No"}</div></div>
    <div class="detail-field"><label>Blocked Reason</label><div class="val">${t.blocked_reason||"None"}</div></div>
    <div class="detail-field"><label>Folder Path</label><div class="val" style="word-break:break-all;font-size:11px">${t.source_folder_path||"N/A"}</div></div>
    <div class="detail-actions">${actions}</div>`;
  document.getElementById("detailOverlay").classList.add("open");
}
function closeDetail(){document.getElementById("detailOverlay").classList.remove("open")}

function getAvailableActions(t){
  const st=t.workflow_stage;
  const btns=[];
  if(t.status==="completed")return"<span style='color:var(--green);font-size:12px'>&#10003; Completed</span>";

  const stageFlow={
    job_setup:          {next:"budget_review",      label:"Submit for Budget Review",           style:"btn-primary"},
    budget_review:      {next:"task_assignment",     label:"Approve Budget",                     style:"btn-green"},
    task_assignment:    {next:"material_check",      label:"Assign Purchaser",                   style:"btn-primary"},
    material_check:     {next:"pricing_validation",  label:"Not in Stock \u2014 Need PO",        style:"btn-amber"},
    pricing_validation: {next:"vendor_coordination", label:"Prices Need Update",                 style:"btn-amber"},
    vendor_coordination:{next:"order_placement",     label:"Coordination Complete",               style:"btn-green"},
    order_placement:    {next:"order_confirmation",  label:"Order Placed",                        style:"btn-green"},
    order_confirmation: {next:"yard_pull",           label:"Confirmation Received",               style:"btn-green"},
    yard_pull:          {next:"material_receiving",  label:"Yard Pull Generated",                 style:"btn-cyan"},
    material_receiving: {next:"completion_check",    label:"Material Arrived",                    style:"btn-green"},
    completion_check:   {next:"completed",           label:"All Material Present \u2014 Complete", style:"btn-green"},
  };

  const flow=stageFlow[st];
  if(flow){
    btns.push(`<button class="btn ${flow.style}" onclick="advanceTask(${t.id},'${flow.next}')">${flow.label}</button>`);
  }

  if(st==="material_check"){
    btns.push(`<button class="btn btn-green" onclick="advanceTask(${t.id},'yard_pull')">In Stock \u2014 Pull from Yard</button>`);
  }
  if(st==="completion_check"){
    btns.push(`<button class="btn btn-amber" onclick="advanceTask(${t.id},'vendor_coordination')">Missing Material \u2014 Reorder</button>`);
  }
  if(t.human_required){
    btns.push(`<button class="btn btn-green" onclick="approveTask(${t.id})">Approve (Financial)</button>`);
    btns.push(`<button class="btn btn-red" onclick="rejectTask(${t.id})">Reject</button>`);
  }
  return btns.join("");
}

async function advanceTask(taskId,nextStage){
  await api("/workflow/advance/"+taskId,{method:"POST",body:JSON.stringify({next_stage:nextStage})});
  closeDetail();await loadAll();
}
async function approveTask(taskId){
  await api("/approvals/financial/"+taskId,{method:"POST",body:JSON.stringify({decision:"approve",notes:"Approved via platform"})});
  closeDetail();await loadAll();
}
async function rejectTask(taskId){
  const reason=prompt("Rejection reason:");if(!reason)return;
  await api("/approvals/financial/"+taskId,{method:"POST",body:JSON.stringify({decision:"reject",notes:reason})});
  closeDetail();await loadAll();
}

// ---- Approvals ----
function renderApprovals(){
  const rows=STATE.approvals||[];
  const badge=document.getElementById("approvalBadge");
  if(rows.length>0){badge.style.display="inline";badge.textContent=rows.length}
  else{badge.style.display="none"}
  document.getElementById("approvalRows").innerHTML=rows.map(r=>{
    const d=r.details||{};
    return`<tr>
      <td>${r.task_id}</td>
      <td>${r.job_number||""}</td>
      <td>${STAGE_LABELS[r.workflow_stage]||r.workflow_stage}</td>
      <td><span class="pill ${r.priority==='high'?'pill-high':'pill-normal'}">${r.priority}</span></td>
      <td style="max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r.blocked_reason||""}</td>
      <td>${d.total!=null?money(d.total):""}</td>
      <td>
        <button class="btn btn-sm btn-green" onclick="approveTask(${r.task_id})">Approve</button>
        <button class="btn btn-sm btn-red" onclick="rejectTask(${r.task_id})">Reject</button>
      </td>
    </tr>`;
  }).join("")||"<tr><td colspan=7 class='empty-state'>No pending approvals</td></tr>";
}

// ---- Vendors ----
function renderVendors(){
  document.getElementById("vendorRows").innerHTML=(STATE.vendors||[]).map(v=>`
    <tr>
      <td>${v.vendor_name||""}</td>
      <td>${v.vendor_code||""}</td>
      <td>${v.vendor_class||""}</td>
      <td>${v.vendor_status||""}</td>
    </tr>`).join("")||"<tr><td colspan=4 class='empty-state'>No vendors loaded</td></tr>";
}

// ---- Activity ----
function renderActivity(){
  document.getElementById("activityList").innerHTML=(STATE.actions||[]).map(a=>`
    <div class="activity-item">
      <div class="activity-dot ${a.action_mode}"></div>
      <div style="flex:1">
        <div class="activity-text"><strong>${a.action_type}</strong> &mdash; Task ${a.task_id||"N/A"}</div>
        <div class="activity-meta">${a.actor_email||"system"} &middot; ${a.action_mode} &middot; ${a.action_status}</div>
        ${a.notes?`<div class="activity-meta" style="margin-top:2px">${a.notes}</div>`:""}
      </div>
    </div>`).join("")||"<div class='empty-state'>No activity recorded</div>";
}

// ---- Intake ----
async function submitIntake(){
  const body={
    job_number:document.getElementById("intakeJobNumber").value||null,
    location:document.getElementById("intakeLocation").value||null,
    vendor:document.getElementById("intakeVendor").value||null,
    budget_amount:parseFloat(document.getElementById("intakeBudget").value)||null,
    po_number:document.getElementById("intakePO").value||null,
    submitted_by:document.getElementById("intakeSubmittedBy").value||null,
    subject:document.getElementById("intakeSubject").value||null,
    notes:document.getElementById("intakeNotes").value||null,
    priority:document.getElementById("intakePriority").value,
    source:document.getElementById("intakeSource").value,
  };
  const res=await api("/intake",{method:"POST",body:JSON.stringify(body)});
  if(res&&res.task_id){
    clearIntakeForm();
    await loadIntakes();
    await loadAll();
  }
}

function clearIntakeForm(){
  ["intakeJobNumber","intakeLocation","intakeVendor","intakeBudget","intakePO","intakeSubmittedBy","intakeSubject","intakeNotes"].forEach(id=>document.getElementById(id).value="");
  document.getElementById("intakePriority").value="normal";
  document.getElementById("intakeSource").value="manual";
}

async function loadIntakes(){
  const rows=await api("/intake/recent?limit=50");
  renderIntakes(rows||[]);
}

function renderIntakes(rows){
  const STAGE_LABELS_LOCAL=Object.fromEntries(ALL_STAGES);
  document.getElementById("intakeRows").innerHTML=rows.map(r=>{
    const d=r.details||{};
    const dateStr=r.created_at?new Date(r.created_at).toLocaleDateString():"";
    return`<tr>
      <td>${r.id}</td>
      <td style="font-weight:600;color:var(--cyan)">${r.job_number||""}</td>
      <td>${d.submitted_by||""}</td>
      <td>${d.vendor||""}</td>
      <td>${d.total!=null?money(d.total):""}</td>
      <td>${STAGE_LABELS_LOCAL[r.workflow_stage]||r.workflow_stage}</td>
      <td><span class="pill ${r.priority==='high'?'pill-high':'pill-normal'}">${r.priority}</span></td>
      <td style="font-size:10px;color:var(--muted)">${d.source||""}</td>
      <td style="font-size:10px;color:var(--muted)">${dateStr}</td>
    </tr>`;
  }).join("")||"<tr><td colspan=9 class='empty-state'>No intake submissions yet</td></tr>";
}

async function refreshAll(){await loadAll();await loadIntakes()}
loadAll();
loadIntakes();
setInterval(()=>{loadAll();loadIntakes()},30000);
</script>
</body>
</html>"""
