from fastapi import FastAPI
from fastapi.responses import HTMLResponse

ui_app = FastAPI(title="Procurement Webapp UI", version="3.0.0")


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
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin-bottom:16px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px}
.kpi-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}
.kpi-value{font-size:24px;font-weight:700}

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

/* Lanes */
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
.card-assignee{font-size:9px;color:var(--cyan);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
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
.detail-panel{width:520px;max-width:92vw;background:var(--sidebar);border-left:1px solid var(--border);height:100vh;overflow-y:auto;padding:20px;animation:slideIn .2s ease}
@keyframes slideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}
.detail-panel h3{font-size:15px;margin-bottom:14px;color:var(--cyan)}
.detail-field{margin-bottom:10px}
.detail-field label{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;display:block;margin-bottom:3px}
.detail-field .val{font-size:13px}

/* Decision Gate Modal */
.gate-modal{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-top:16px}
.gate-modal h4{font-size:13px;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:8px}
.gate-modal h4 .diamond-sm{width:10px;height:10px;background:var(--cyan);transform:rotate(45deg);border-radius:2px;flex-shrink:0}
.gate-question{font-size:12px;color:var(--text);margin-bottom:10px;line-height:1.5}
.gate-options{display:flex;flex-direction:column;gap:8px}
.gate-option{display:flex;align-items:center;gap:12px;padding:10px 14px;background:var(--bg);border:1px solid var(--border);border-radius:8px;cursor:pointer;transition:all .15s}
.gate-option:hover{border-color:var(--cyan);background:var(--surface2)}
.gate-option .opt-icon{font-size:18px;flex-shrink:0}
.gate-option .opt-label{font-size:12px;font-weight:600}
.gate-option .opt-desc{font-size:10px;color:var(--muted);margin-top:2px}
.gate-form{margin-top:10px;display:flex;flex-direction:column;gap:8px}
.gate-form .form-row{display:flex;flex-direction:column;gap:3px}
.gate-form .form-row label{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.gate-form .form-row input,.gate-form .form-row select,.gate-form .form-row textarea{background:var(--bg);border:1px solid var(--border);color:var(--text);padding:8px 10px;border-radius:6px;font-size:12px;transition:border-color .15s}
.gate-form .form-row input:focus,.gate-form .form-row select:focus,.gate-form .form-row textarea:focus{outline:none;border-color:var(--blue)}
.gate-form-2col{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.gate-submit{margin-top:10px;display:flex;gap:8px}
.gate-submit .btn{flex:1}

/* Workflow Path Tracker */
.path-tracker{display:flex;align-items:center;gap:0;margin:14px 0;flex-wrap:wrap;gap:2px}
.path-step{display:flex;align-items:center;gap:0;font-size:10px}
.path-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.path-dot.done{background:var(--green)}
.path-dot.current{background:var(--cyan);box-shadow:0 0 6px var(--cyan)}
.path-dot.pending{background:var(--gray)}
.path-label{padding:0 6px;color:var(--muted);white-space:nowrap}
.path-label.current{color:var(--cyan);font-weight:600}
.path-label.done{color:var(--green)}
.path-arrow{color:var(--gray);font-size:10px;padding:0 2px}
.path-decision{display:inline-flex;align-items:center;gap:3px;font-size:10px;color:var(--amber);margin:1px 2px}
.path-decision .d-icon{width:8px;height:8px;background:var(--amber);transform:rotate(45deg);border-radius:1px;flex-shrink:0;opacity:.7}

/* Timeline */
.timeline{margin-top:16px;border-top:1px solid var(--border);padding-top:14px}
.timeline h4{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px}
.tl-item{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid rgba(30,42,50,.5)}
.tl-dot{width:7px;height:7px;border-radius:50%;margin-top:5px;flex-shrink:0}
.tl-dot.evt-intake{background:var(--blue)}
.tl-dot.evt-budget{background:var(--amber)}
.tl-dot.evt-assign{background:var(--cyan)}
.tl-dot.evt-material{background:var(--green)}
.tl-dot.evt-order{background:var(--amber)}
.tl-dot.evt-complete{background:var(--green)}
.tl-dot.evt-default{background:var(--muted)}
.tl-text{font-size:11px;flex:1}
.tl-meta{font-size:9px;color:var(--muted);margin-top:2px}

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

/* Toast */
.toast{position:fixed;bottom:20px;right:20px;padding:10px 16px;border-radius:8px;font-size:12px;font-weight:600;z-index:999;animation:fadeUp .3s ease;color:#fff}
.toast.success{background:var(--green)}
.toast.error{background:var(--red)}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

@media(max-width:900px){
  .sidebar{width:56px}
  .sidebar-brand img{height:24px}
  .sidebar-brand .brand-text,.sidebar-brand .brand-sub,.nav-section,.nav-item span:not(.icon),.sidebar-footer label{display:none}
  .main{margin-left:56px}
  .nav-item{justify-content:center;padding:10px}
}
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
      <div class="kpi-row" id="kpiRow"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
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
      <div id="jobBoard"></div>
    </div>

    <!-- APPROVALS -->
    <div class="page" id="page-approvals">
      <div class="table-wrap">
        <table class="data-table">
          <thead><tr><th>Task</th><th>Job</th><th>Stage</th><th>Assignee</th><th>Priority</th><th>Reason</th><th>Amount</th><th>Action</th></tr></thead>
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
              <thead><tr><th>ID</th><th>Job #</th><th>Submitted By</th><th>Vendor</th><th>Amount</th><th>Stage</th><th>Assignee</th><th>Priority</th><th>Source</th><th>Date</th></tr></thead>
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

// Purchaser roster (from org chart)
const PURCHASERS=[
  {email:"tiffany.myers@hurricanefence.com",name:"Tiffany Myers",role:"Director of Purchasing"},
  {email:"amy.shelton@hurricanefence.com",name:"Amy Shelton",role:"Purchaser"},
  {email:"aysia.myers@hurricanefence.com",name:"Aysia Myers",role:"Purchaser"},
  {email:"taylor.brookins@hurricanefence.com",name:"Taylor Brookins",role:"Purchaser"},
];

const PROCESS_GROUPS=[
  {
    id:"initiation",name:"Job Initiation & Budget",color:"var(--blue)",
    desc:"PMA submits job with budget. PM reviews budget quality. If good, assign to purchaser.",
    decision:"Budget Good? \u2192 Yes: Assign Purchaser | No: PM Revises Budget",
    stages:[["job_setup","Job Setup"],["budget_review","Budget Review"]]
  },
  {
    id:"assignment",name:"Assignment & Material Check",color:"var(--cyan)",
    desc:"PM assigns purchaser. Purchaser checks: Is material in stock? Can we pull from extra materials?",
    decision:"In Stock or Extra Available? \u2192 Yes: Yard Pull | No: Procurement Path",
    stages:[["task_assignment","Task Assignment"],["material_check","Material Check"]]
  },
  {
    id:"procurement",name:"Procurement & Ordering",color:"var(--amber)",
    desc:"Check if PO was provided and prices are valid. Coordinate with vendor on price, delivery, location. Place order.",
    decision:"PO Provided & Prices Valid? \u2192 Yes: Order | No: Vendor Coordination",
    stages:[["pricing_validation","Pricing / PO Check"],["vendor_coordination","Vendor Coordination"],["order_placement","Order Placement"]]
  },
  {
    id:"fulfillment",name:"Fulfillment & Closeout",color:"var(--green)",
    desc:"Confirm order, await delivery, generate yard pull, verify all material is present. Complete job.",
    decision:"All Material Present? \u2192 Yes: Job Scheduled | No: Confirm Backorder with Vendor",
    stages:[["order_confirmation","Order Confirmation"],["yard_pull","Yard Pull"],["material_receiving","Material Receiving"],["completion_check","Completion Check"],["completed","Completed"]]
  }
];

const ALL_STAGES=PROCESS_GROUPS.flatMap(g=>g.stages);
const STAGE_LABELS=Object.fromEntries(ALL_STAGES);

let STATE={tasks:[],approvals:[],vendors:[],actions:[],summary:{}};
let collapsedGroups={};

function headers(){return{"X-User-Email":document.getElementById("userEmail").value,"Content-Type":"application/json"}}
function money(v){return"$"+Number(v||0).toLocaleString(undefined,{maximumFractionDigits:0})}
function esc(s){const d=document.createElement("div");d.textContent=s||"";return d.innerHTML}

function toast(msg,type){
  type=type||"success";
  const el=document.createElement("div");el.className="toast "+type;el.textContent=msg;
  document.body.appendChild(el);setTimeout(function(){el.remove()},3000);
}

async function api(path,opts){
  opts=opts||{};
  const res=await fetch(API+path,{headers:headers(),...opts});
  if(!res.ok){
    if(opts.allow403&&res.status===403)return null;
    console.warn(path,res.status);return null;
  }
  return res.json();
}

document.querySelectorAll(".nav-item").forEach(function(btn){
  btn.addEventListener("click",function(){
    document.querySelectorAll(".nav-item").forEach(function(b){b.classList.remove("active")});
    btn.classList.add("active");
    var pg=btn.dataset.page;
    document.querySelectorAll(".page").forEach(function(p){p.classList.remove("active")});
    document.getElementById("page-"+pg).classList.add("active");
    document.getElementById("pageTitle").textContent=btn.querySelector("span:last-child").textContent;
  });
});

async function loadAll(){
  var results=await Promise.all([
    api("/dashboard/summary"),
    api("/tasks?limit=500"),
    api("/approvals/financial?limit=200",{allow403:true}),
    api("/vendors?limit=500"),
    api("/workflow/actions/recent?limit=100"),
  ]);
  STATE.summary=results[0]||{};
  STATE.tasks=results[1]||[];
  STATE.approvals=results[2]||[];
  STATE.vendors=results[3]||[];
  STATE.actions=results[4]||[];
  renderDashboard();renderBoard();renderApprovals();renderVendors();renderActivity();
}

// ---- Dashboard ----
function renderDashboard(){
  var s=STATE.summary;
  var kpis=[
    {label:"Open Jobs",value:s.open_tasks||0,color:"var(--blue)"},
    {label:"Budget Review",value:s.awaiting_budget_review||0,color:"var(--amber)"},
    {label:"Awaiting Assignment",value:s.awaiting_assignment||0,color:"var(--cyan)"},
    {label:"In Procurement",value:s.in_procurement||0,color:"var(--amber)"},
    {label:"In Fulfillment",value:s.in_fulfillment||0,color:"var(--green)"},
    {label:"High Priority",value:s.open_high_priority_tasks||0,color:"var(--red)"},
    {label:"Tracked PO Spend",value:money(s.tracked_po_spend),color:"var(--green)"},
  ];
  document.getElementById("kpiRow").innerHTML=kpis.map(function(k){return '<div class="kpi"><div class="kpi-label">'+esc(k.label)+'</div><div class="kpi-value" style="color:'+k.color+'">'+k.value+'</div></div>'}).join("");

  var stageCounts={};
  STATE.tasks.forEach(function(t){var st=t.workflow_stage||"unknown";stageCounts[st]=(stageCounts[st]||0)+1});

  var tableHtml="";
  PROCESS_GROUPS.forEach(function(g){
    g.stages.forEach(function(pair,i){
      var key=pair[0],label=pair[1];
      var n=stageCounts[key]||0;
      tableHtml+='<tr><td>'+(i===0?'<span style="color:'+g.color+';font-weight:700">'+esc(g.name)+'</span>':"")+'</td><td>'+esc(label)+'</td><td style="font-weight:600">'+n+'</td></tr>';
    });
  });
  document.getElementById("stageTable").innerHTML=tableHtml||"<tr><td colspan=3 class='empty-state'>No data</td></tr>";

  document.getElementById("dashActivity").innerHTML=(STATE.actions||[]).slice(0,12).map(function(a){
    return '<div class="activity-item"><div class="activity-dot '+a.action_mode+'"></div><div><div class="activity-text"><strong>'+esc(a.action_type)+'</strong> on Task '+(a.task_id||"")+'</div><div class="activity-meta">'+esc(a.actor_email||"system")+' &middot; '+esc(a.action_mode)+'</div></div></div>';
  }).join("")||"<div class='empty-state'>No recent activity</div>";
}

// ---- Job Board ----
function renderBoard(){
  var byStage={};
  ALL_STAGES.forEach(function(pair){byStage[pair[0]]=[]});
  STATE.tasks.forEach(function(t){
    var st=t.workflow_stage||"job_setup";
    if(!byStage[st])byStage[st]=[];
    byStage[st].push(t);
  });

  document.getElementById("jobBoard").innerHTML=PROCESS_GROUPS.map(function(g,gi){
    var groupTotal=g.stages.reduce(function(s,pair){return s+(byStage[pair[0]]||[]).length},0);
    var humanCount=g.stages.reduce(function(s,pair){return s+(byStage[pair[0]]||[]).filter(function(t){return t.human_required}).length},0);
    var isCollapsed=collapsedGroups[g.id];

    var lanes=g.stages.map(function(pair){
      var key=pair[0],label=pair[1];
      var items=byStage[key]||[];
      var cards=items.slice(0,25).map(function(t){return renderCard(t)}).join("");
      var overflow=items.length>25?'<div style="padding:5px;font-size:10px;color:var(--muted);text-align:center">+'+(items.length-25)+' more</div>':"";
      return '<div class="lane"><div class="lane-header"><span class="lane-title">'+esc(label)+'</span><span class="lane-count">'+items.length+'</span></div><div class="lane-body">'+(cards||"<div class='empty-state'>Empty</div>")+overflow+'</div></div>';
    }).join("");

    return '<div class="process-group"><div class="process-header" onclick="toggleGroup(\''+g.id+'\')"><div><div class="process-title"><div class="process-num" style="background:'+g.color+'">'+(gi+1)+'</div><span class="process-name">'+esc(g.name)+'</span></div><div class="process-desc">'+esc(g.desc)+'</div></div><div class="process-stats"><span><strong style="color:var(--text)">'+groupTotal+'</strong> jobs</span>'+(humanCount?'<span><strong style="color:var(--amber)">'+humanCount+'</strong> need action</span>':"")+'<span style="font-size:14px">'+(isCollapsed?"\u25B6":"\u25BC")+'</span></div></div><div class="process-body'+(isCollapsed?" collapsed":"")+'">'+lanes+'</div><div class="decision-gate"><div class="diamond"></div><span>'+esc(g.decision)+'</span></div></div>';
  }).join("");
}

function renderCard(t){
  var d=t.details||{};
  var pri=t.priority==="high"?"pill-high":"pill-normal";
  return '<div class="card" onclick="openDetail('+t.id+')"><div class="card-job">'+esc(t.job_number||"No Job #")+'</div><div class="card-vendor">'+esc(d.vendor||"Unknown vendor")+'</div><div class="card-row"><span class="pill '+pri+'">'+esc(t.priority)+'</span><span class="card-amount">'+(d.total!=null?money(d.total):"")+'</span></div>'+(t.human_required?'<div class="card-row" style="margin-top:3px"><span class="pill pill-human">Action Needed</span></div>':"")+(t.assigned_purchaser_email?'<div class="card-assignee">'+esc(t.assigned_purchaser_email.split("@")[0])+'</div>':"")+'</div>';
}

function toggleGroup(id){collapsedGroups[id]=!collapsedGroups[id];renderBoard()}

// ---- Detail Panel with Decision Gates ----

async function openDetail(taskId){
  var res=await api("/tasks/"+taskId);
  if(!res)return;
  var t=res.task;
  var events=res.events||[];
  var d=t.details||{};
  var stage=STAGE_LABELS[t.workflow_stage]||t.workflow_stage;
  var group=PROCESS_GROUPS.find(function(g){return g.stages.some(function(pair){return pair[0]===t.workflow_stage})});

  var html='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px"><h3>Task #'+t.id+(t.status==="completed"?' <span style="color:var(--green);font-size:12px;margin-left:8px">&#10003; Completed</span>':"")+'</h3><button class="btn btn-sm" onclick="closeDetail()">Close</button></div>';
  if(group)html+='<div style="margin-bottom:14px;padding:8px 10px;border-radius:6px;background:var(--surface2);font-size:11px;color:var(--muted)"><strong style="color:'+group.color+'">'+esc(group.name)+'</strong> &middot; '+esc(stage)+'</div>';

  html+=renderPathTracker(t);

  html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><div class="detail-field"><label>Job Number</label><div class="val">'+esc(t.job_number||"N/A")+'</div></div><div class="detail-field"><label>Priority</label><div class="val"><span class="pill '+(t.priority==="high"?"pill-high":"pill-normal")+'">'+esc(t.priority)+'</span></div></div><div class="detail-field"><label>Vendor</label><div class="val">'+esc(d.vendor||"N/A")+'</div></div><div class="detail-field"><label>Amount</label><div class="val">'+(d.total!=null?money(d.total):"N/A")+'</div></div><div class="detail-field"><label>PO Number</label><div class="val">'+esc(d.po_number||"N/A")+'</div></div><div class="detail-field"><label>Location</label><div class="val">'+esc(d.location||t.source_folder_path||"N/A")+'</div></div></div>';

  if(t.assigned_purchaser_email)html+='<div class="detail-field"><label>Assigned Purchaser</label><div class="val" style="color:var(--cyan)">'+esc(t.assigned_purchaser_email)+'</div></div>';
  if(t.blocked_reason)html+='<div class="detail-field"><label>Status</label><div class="val" style="color:var(--amber)">'+esc(t.blocked_reason)+'</div></div>';

  if(t.status!=="completed")html+=renderDecisionGate(t);

  if(events.length>0){
    html+='<div class="timeline"><h4>Timeline</h4>';
    events.forEach(function(e){
      var cls=e.event_type.indexOf("intake")>=0?"evt-intake":e.event_type.indexOf("budget")>=0?"evt-budget":e.event_type.indexOf("assign")>=0||e.event_type.indexOf("purchaser")>=0?"evt-assign":e.event_type.indexOf("material")>=0||e.event_type.indexOf("yard")>=0?"evt-material":e.event_type.indexOf("order")>=0||e.event_type.indexOf("vendor")>=0||e.event_type.indexOf("pricing")>=0?"evt-order":e.event_type.indexOf("complet")>=0?"evt-complete":"evt-default";
      html+='<div class="tl-item"><div class="tl-dot '+cls+'"></div><div><div class="tl-text"><strong>'+esc(e.event_type)+'</strong></div><div class="tl-meta">'+esc(e.notes||"")+'</div>'+(e.at?'<div class="tl-meta">'+new Date(e.at).toLocaleString()+'</div>':"")+'</div></div>';
    });
    html+='</div>';
  }

  document.getElementById("detailPanel").innerHTML=html;
  document.getElementById("detailOverlay").classList.add("open");
}

function closeDetail(){document.getElementById("detailOverlay").classList.remove("open")}

// ---- Path Tracker ----
function renderPathTracker(t){
  var stageOrder=["job_setup","budget_review","task_assignment","material_check","pricing_validation","vendor_coordination","order_placement","order_confirmation","yard_pull","completion_check","completed"];
  var stageShort={job_setup:"Setup",budget_review:"Budget",task_assignment:"Assign",material_check:"Material",pricing_validation:"Pricing",vendor_coordination:"Vendor",order_placement:"Order",order_confirmation:"Confirm",yard_pull:"Yard Pull",completion_check:"Check",completed:"Done"};
  var decisions=t.decision_path||[];
  var visited={job_setup:true};
  decisions.forEach(function(d){if(d.stage)visited[d.stage]=true});
  if(t.workflow_stage)visited[t.workflow_stage]=true;

  var html='<div class="path-tracker">';
  stageOrder.forEach(function(s,i){
    var isCurrent=s===t.workflow_stage;
    var isDone=visited[s]&&!isCurrent;
    var cls=isCurrent?"current":isDone?"done":"pending";
    if(i>0)html+='<span class="path-arrow">\u2192</span>';
    html+='<span class="path-step"><span class="path-dot '+cls+'"></span><span class="path-label '+cls+'">'+(stageShort[s]||s)+'</span></span>';
  });
  html+="</div>";
  if(decisions.length>0){
    html+='<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:14px">';
    decisions.forEach(function(d){html+='<span class="path-decision"><span class="d-icon"></span>'+esc(d.decision)+'</span>'});
    html+="</div>";
  }
  return html;
}

// ---- Decision Gate Rendering ----
function renderDecisionGate(t){
  var st=t.workflow_stage;
  if(st==="job_setup"||st==="budget_review")return renderBudgetGate(t);
  if(st==="task_assignment")return renderAssignmentGate(t);
  if(st==="material_check")return renderMaterialGate(t);
  if(st==="pricing_validation")return renderPricingGate(t);
  if(st==="vendor_coordination")return renderVendorCoordGate(t);
  if(st==="order_placement")return renderOrderGate(t);
  if(st==="order_confirmation")return renderConfirmGate(t);
  if(st==="yard_pull"||st==="material_receiving")return renderArrivalGate(t);
  if(st==="completion_check")return renderCompletionGate(t);
  return "";
}

function renderBudgetGate(t){
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>Budget Quality Check</h4><div class="gate-question">Review the budget submitted by PMA. Is the budget correct and complete?</div><div class="gate-options"><div class="gate-option" onclick="doBudgetReview('+t.id+',true)"><span class="opt-icon" style="color:var(--green)">&#10003;</span><div><div class="opt-label">Budget Good</div><div class="opt-desc">Approve budget and proceed to assign a purchaser</div></div></div><div class="gate-option" onclick="showBudgetReject()"><span class="opt-icon" style="color:var(--red)">&#10007;</span><div><div class="opt-label">Quality Errors</div><div class="opt-desc">Send back to Project Manager for revision</div></div></div></div><div id="budgetRejectForm" style="display:none" class="gate-form"><div class="form-row"><label>Describe the quality errors</label><textarea id="budgetErrors" rows="3" placeholder="Missing line items, incorrect pricing, etc."></textarea></div><div class="gate-submit"><button class="btn btn-red" onclick="doBudgetReview('+t.id+',false)">Send Back for Revision</button></div></div></div>';
}

function showBudgetReject(){document.getElementById("budgetRejectForm").style.display="flex"}

async function doBudgetReview(taskId,good){
  var errors=good?null:(document.getElementById("budgetErrors")||{}).value;
  var res=await api("/workflow/budget-review/"+taskId,{method:"POST",body:JSON.stringify({budget_good:good,quality_errors:errors})});
  if(res){toast(good?"Budget approved":"Budget sent back for revision",good?"success":"error");closeDetail();await loadAll()}
}

function renderAssignmentGate(t){
  var opts=PURCHASERS.map(function(p){return '<option value="'+esc(p.email)+'">'+esc(p.name)+' ('+esc(p.role)+')</option>'}).join("");
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>Assign Purchaser</h4><div class="gate-question">Select a purchaser to handle this job\'s material procurement.</div><div class="gate-form"><div class="form-row"><label>Purchaser</label><select id="assignPurchaser">'+opts+'</select></div><div class="form-row"><label>Notes (optional)</label><input type="text" id="assignNotes" placeholder="Any special instructions"/></div><div class="gate-submit"><button class="btn btn-primary" onclick="doAssign('+t.id+')">Assign Purchaser</button></div></div></div>';
}

async function doAssign(taskId){
  var email=document.getElementById("assignPurchaser").value;
  var notes=document.getElementById("assignNotes").value||null;
  var res=await api("/workflow/assign-purchaser/"+taskId,{method:"POST",body:JSON.stringify({purchaser_email:email,notes:notes})});
  if(res){toast("Purchaser assigned: "+email.split("@")[0]);closeDetail();await loadAll()}
}

function renderMaterialGate(t){
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>Material Availability Check</h4><div class="gate-question">Check inventory: Is the material in stock? Can we pull from extra materials on hand?</div><div class="gate-options"><div class="gate-option" onclick="doMaterialCheck('+t.id+',true,false)"><span class="opt-icon" style="color:var(--green)">&#9745;</span><div><div class="opt-label">In Stock</div><div class="opt-desc">Material is available in yard inventory. Generate yard pull.</div></div></div><div class="gate-option" onclick="doMaterialCheck('+t.id+',false,true)"><span class="opt-icon" style="color:var(--cyan)">&#9881;</span><div><div class="opt-label">Pull from Extra Materials</div><div class="opt-desc">Reserve materials from surplus. Create sales order and tag material.</div></div></div><div class="gate-option" onclick="doMaterialCheck('+t.id+',false,false)"><span class="opt-icon" style="color:var(--amber)">&#10060;</span><div><div class="opt-label">Not Available</div><div class="opt-desc">Not in stock and no extras. Proceed to procurement (PO/vendor check).</div></div></div></div></div>';
}

async function doMaterialCheck(taskId,inStock,canPull){
  var res=await api("/workflow/material-check/"+taskId,{method:"POST",body:JSON.stringify({material_in_stock:inStock,can_pull_extra:canPull})});
  if(res){var msg=inStock?"In stock - yard pull generated":canPull?"Extra materials reserved":"Proceeding to procurement";toast(msg);closeDetail();await loadAll()}
}

function renderPricingGate(t){
  var d=t.details||{};
  var hasPO=!!(d.po_number);
  var poHint=hasPO?'<div style="padding:6px 10px;background:rgba(23,220,239,.06);border-radius:6px;margin-bottom:10px;font-size:11px;color:var(--cyan)">PO detected from intake: <strong>'+esc(d.po_number)+'</strong></div>':"";
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>PO & Pricing Validation</h4><div class="gate-question">Was a PO provided with this job? If yes, are the prices still valid?</div>'+poHint+'<div class="gate-options"><div class="gate-option" onclick="doPricingCheck('+t.id+',true,true)"><span class="opt-icon" style="color:var(--green)">&#10003;</span><div><div class="opt-label">PO Provided + Prices Valid</div><div class="opt-desc">Proceed directly to place order</div></div></div><div class="gate-option" onclick="doPricingCheck('+t.id+',true,false)"><span class="opt-icon" style="color:var(--amber)">&#9888;</span><div><div class="opt-label">PO Provided but Prices Outdated</div><div class="opt-desc">Need to coordinate with vendor for updated pricing</div></div></div><div class="gate-option" onclick="doPricingCheck('+t.id+',false,null)"><span class="opt-icon" style="color:var(--red)">&#10060;</span><div><div class="opt-label">No PO Provided</div><div class="opt-desc">Need full vendor coordination: price, delivery time, delivery location</div></div></div></div></div>';
}

async function doPricingCheck(taskId,po,prices){
  var res=await api("/workflow/pricing-check/"+taskId,{method:"POST",body:JSON.stringify({po_provided:po,prices_valid:prices})});
  if(res){var msg=po&&prices?"Ready to order":po?"Prices outdated - vendor coordination":"No PO - vendor coordination needed";toast(msg);closeDetail();await loadAll()}
}

function renderVendorCoordGate(t){
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>Vendor Coordination</h4><div class="gate-question">Coordinate with vendor on the following. Fill in the details once confirmed.</div><div class="gate-form"><div class="gate-form-2col"><div class="form-row"><label>Negotiated Price</label><input type="text" id="vcPrice" placeholder="e.g. $4,500"/></div><div class="form-row"><label>Delivery Time</label><input type="text" id="vcDelivery" placeholder="e.g. 5 business days"/></div></div><div class="form-row"><label>Delivery Location</label><input type="text" id="vcLocation" placeholder="e.g. Hurricane Fence yard, Richmond VA"/></div><div class="form-row"><label>Notes</label><textarea id="vcNotes" rows="2" placeholder="Any additional coordination notes"></textarea></div><div class="gate-submit"><button class="btn btn-green" onclick="doVendorCoord('+t.id+')">Coordination Complete - Ready to Order</button></div></div></div>';
}

async function doVendorCoord(taskId){
  var body={price:document.getElementById("vcPrice").value||null,delivery_time:document.getElementById("vcDelivery").value||null,delivery_location:document.getElementById("vcLocation").value||null,notes:document.getElementById("vcNotes").value||null};
  var res=await api("/workflow/vendor-coordination/"+taskId,{method:"POST",body:JSON.stringify(body)});
  if(res){toast("Vendor coordination complete");closeDetail();await loadAll()}
}

function renderOrderGate(t){
  var coordInfo=t.vendor_coord_price?'<div style="font-size:11px;color:var(--muted);margin-bottom:8px">Price: <strong style="color:var(--text)">'+esc(t.vendor_coord_price)+'</strong> | Delivery: <strong style="color:var(--text)">'+esc(t.vendor_coord_delivery_time||"TBD")+'</strong> | Location: <strong style="color:var(--text)">'+esc(t.vendor_coord_delivery_location||"TBD")+'</strong></div>':"";
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>Place Order</h4><div class="gate-question">All details confirmed. Place the order with the vendor.</div>'+coordInfo+'<div class="gate-submit"><button class="btn btn-green" onclick="doPlaceOrder('+t.id+')" style="flex:1">Order Material</button></div></div>';
}

async function doPlaceOrder(taskId){
  var res=await api("/workflow/place-order/"+taskId,{method:"POST"});
  if(res){toast("Order placed - awaiting confirmation");closeDetail();await loadAll()}
}

function renderConfirmGate(t){
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>Order Confirmation & Lead Times</h4><div class="gate-question">Has the vendor confirmed the order? Enter the expected delivery date.</div><div class="gate-form"><div class="form-row"><label>Expected Delivery Date</label><input type="date" id="confirmDate"/></div><div class="gate-submit"><button class="btn btn-green" onclick="doConfirmOrder('+t.id+')">Confirmation Received - Generate Yard Pull</button></div></div></div>';
}

async function doConfirmOrder(taskId){
  var dt=document.getElementById("confirmDate").value||"";
  var res=await api("/workflow/confirm-order/"+taskId+"?expected_delivery_date="+encodeURIComponent(dt),{method:"POST"});
  if(res){toast("Order confirmed - yard pull generated");closeDetail();await loadAll()}
}

function renderArrivalGate(t){
  var dateHint=t.expected_delivery_date?" Expected: <strong>"+new Date(t.expected_delivery_date).toLocaleDateString()+"</strong>":"";
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>Material Arrival</h4><div class="gate-question">Has the material arrived at the yard?'+dateHint+'</div><div class="gate-submit"><button class="btn btn-green" onclick="doMaterialArrives('+t.id+')" style="flex:1">Material Has Arrived</button></div></div>';
}

async function doMaterialArrives(taskId){
  var res=await api("/workflow/material-arrives/"+taskId,{method:"POST"});
  if(res){toast("Material arrived - checking completeness");closeDetail();await loadAll()}
}

function renderCompletionGate(t){
  return '<div class="gate-modal"><h4><span class="diamond-sm"></span>All Material Present?</h4><div class="gate-question">Verify that ALL required material for this job has been received. Is everything present?</div><div class="gate-options"><div class="gate-option" onclick="doCompletionCheck('+t.id+',true)"><span class="opt-icon" style="color:var(--green)">&#10003;</span><div><div class="opt-label">All Material Present</div><div class="opt-desc">Job is ready to be scheduled. Mark as complete.</div></div></div><div class="gate-option" onclick="showBackorderForm()"><span class="opt-icon" style="color:var(--amber)">&#9888;</span><div><div class="opt-label">Missing Material</div><div class="opt-desc">Confirm with vendor on arrival date for back-ordered materials</div></div></div></div><div id="backorderForm" style="display:none" class="gate-form"><div class="form-row"><label>Back-order details (what is missing)</label><textarea id="backorderNotes" rows="3" placeholder="Missing items, quantities, etc."></textarea></div><div class="form-row"><label>Expected Arrival Date</label><input type="date" id="backorderDate"/></div><div class="gate-submit"><button class="btn btn-amber" onclick="doCompletionCheck('+t.id+',false)">Confirm Backorder - Return to Vendor Coordination</button></div></div></div>';
}

function showBackorderForm(){document.getElementById("backorderForm").style.display="flex"}

async function doCompletionCheck(taskId,allPresent){
  var body={all_material_present:allPresent};
  if(!allPresent){body.backorder_notes=(document.getElementById("backorderNotes")||{}).value||null;body.expected_delivery_date=(document.getElementById("backorderDate")||{}).value||null}
  var res=await api("/workflow/completion-check/"+taskId,{method:"POST",body:JSON.stringify(body)});
  if(res){toast(allPresent?"Job complete - scheduled!":"Back to vendor for missing material",allPresent?"success":"error");closeDetail();await loadAll()}
}

// ---- Approvals ----
function renderApprovals(){
  var rows=STATE.approvals||[];
  var badge=document.getElementById("approvalBadge");
  if(rows.length>0){badge.style.display="inline";badge.textContent=rows.length}else{badge.style.display="none"}
  document.getElementById("approvalRows").innerHTML=rows.map(function(r){
    var d=r.details||{};
    return '<tr><td><a href="#" onclick="openDetail('+r.task_id+');return false" style="color:var(--cyan)">'+r.task_id+'</a></td><td>'+esc(r.job_number||"")+'</td><td>'+esc(STAGE_LABELS[r.workflow_stage]||r.workflow_stage)+'</td><td style="color:var(--cyan)">'+esc((d||{}).assigned_purchaser||"")+'</td><td><span class="pill '+(r.priority==="high"?"pill-high":"pill-normal")+'">'+esc(r.priority)+'</span></td><td style="max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+esc(r.blocked_reason||"")+'</td><td>'+(d.total!=null?money(d.total):"")+'</td><td><button class="btn btn-sm btn-cyan" onclick="openDetail('+r.task_id+')">Review</button></td></tr>';
  }).join("")||"<tr><td colspan=8 class='empty-state'>No pending approvals</td></tr>";
}

// ---- Vendors ----
function renderVendors(){
  document.getElementById("vendorRows").innerHTML=(STATE.vendors||[]).map(function(v){return '<tr><td>'+esc(v.vendor_name||"")+'</td><td>'+esc(v.vendor_code||"")+'</td><td>'+esc(v.vendor_class||"")+'</td><td>'+esc(v.vendor_status||"")+'</td></tr>'}).join("")||"<tr><td colspan=4 class='empty-state'>No vendors loaded</td></tr>";
}

// ---- Activity ----
function renderActivity(){
  document.getElementById("activityList").innerHTML=(STATE.actions||[]).map(function(a){return '<div class="activity-item"><div class="activity-dot '+a.action_mode+'"></div><div style="flex:1"><div class="activity-text"><strong>'+esc(a.action_type)+'</strong> &mdash; Task '+(a.task_id||"N/A")+'</div><div class="activity-meta">'+esc(a.actor_email||"system")+' &middot; '+esc(a.action_mode)+' &middot; '+esc(a.action_status)+'</div>'+(a.notes?'<div class="activity-meta" style="margin-top:2px">'+esc(a.notes)+'</div>':"")+'</div></div>'}).join("")||"<div class='empty-state'>No activity recorded</div>";
}

// ---- Intake ----
async function submitIntake(){
  var body={job_number:document.getElementById("intakeJobNumber").value||null,location:document.getElementById("intakeLocation").value||null,vendor:document.getElementById("intakeVendor").value||null,budget_amount:parseFloat(document.getElementById("intakeBudget").value)||null,po_number:document.getElementById("intakePO").value||null,submitted_by:document.getElementById("intakeSubmittedBy").value||null,subject:document.getElementById("intakeSubject").value||null,notes:document.getElementById("intakeNotes").value||null,priority:document.getElementById("intakePriority").value,source:document.getElementById("intakeSource").value};
  var res=await api("/intake",{method:"POST",body:JSON.stringify(body)});
  if(res&&res.task_id){toast("Job submitted to board");clearIntakeForm();await loadIntakes();await loadAll()}
}

function clearIntakeForm(){
  ["intakeJobNumber","intakeLocation","intakeVendor","intakeBudget","intakePO","intakeSubmittedBy","intakeSubject","intakeNotes"].forEach(function(id){document.getElementById(id).value=""});
  document.getElementById("intakePriority").value="normal";document.getElementById("intakeSource").value="manual";
}

async function loadIntakes(){
  var rows=await api("/intake/recent?limit=50");
  renderIntakes(rows||[]);
}

function renderIntakes(rows){
  document.getElementById("intakeRows").innerHTML=rows.map(function(r){
    var d=r.details||{};
    var dateStr=r.created_at?new Date(r.created_at).toLocaleDateString():"";
    return '<tr><td>'+r.id+'</td><td style="font-weight:600;color:var(--cyan)">'+esc(r.job_number||"")+'</td><td>'+esc(d.submitted_by||"")+'</td><td>'+esc(d.vendor||"")+'</td><td>'+(d.total!=null?money(d.total):"")+'</td><td>'+esc(STAGE_LABELS[r.workflow_stage]||r.workflow_stage)+'</td><td style="color:var(--cyan)">'+esc(r.assigned_purchaser_email||"")+'</td><td><span class="pill '+(r.priority==="high"?"pill-high":"pill-normal")+'">'+esc(r.priority)+'</span></td><td style="font-size:10px;color:var(--muted)">'+esc(d.source||"")+'</td><td style="font-size:10px;color:var(--muted)">'+dateStr+'</td></tr>';
  }).join("")||"<tr><td colspan=10 class='empty-state'>No intake submissions yet</td></tr>";
}

async function refreshAll(){await loadAll();await loadIntakes()}
loadAll();loadIntakes();
setInterval(function(){loadAll();loadIntakes()},30000);
</script>
</body>
</html>"""
