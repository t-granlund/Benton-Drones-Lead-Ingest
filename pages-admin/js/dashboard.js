/* Benton Drones Pages Admin Dashboard (ADR-001).
 * Talks to the Render API with `credentials: "include"` so the CF_Authorization
 * cookie (set by Cloudflare Access on the .bentondrones.com domain) flows
 * cross-origin; Cloudflare edge then injects Cf-Access-Jwt-Assertion which the
 * backend verifies. No tokens are stored in the browser by this code. */
(function () {
  "use strict";

  var API = (window.ADMIN_API_BASE || "").replace(/\/+$/, "");
  var $ = function (id) { return document.getElementById(id); };

  function fail(msg) {
    $("loading").style.display = "none";
    var box = $("error");
    box.style.display = "block";
    box.textContent = "Dashboard error: " + msg +
      " — check that Cloudflare Access is protecting both this site and the API, " +
      "and that CORS_ADMIN_ORIGIN is set on the backend.";
  }

  function api(path) {
    return fetch(API + path, { credentials: "include", headers: { "Accept": "application/json" } })
      .then(function (r) {
        if (r.status === 401 || r.status === 403) throw new Error("HTTP " + r.status + " (auth)");
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      });
  }

  function esc(s) {
    var d = document.createElement("div");
    d.appendChild(document.createTextNode(s == null ? "" : String(s)));
    return d.innerHTML;
  }

  function metric(label, value) {
    return '<div class="metric"><div class="value">' + esc(value) +
      '</div><div class="label">' + esc(label) + "</div></div>";
  }

  function breakdown(id, obj) {
    var parts = Object.keys(obj || {}).map(function (k) {
      return "<span>" + esc(k || "unset") + " (" + esc(obj[k]) + ")</span>";
    });
    $(id).innerHTML = parts.length ? parts.join(" ") : "<em>No data</em>";
  }

  function renderSummary(s) {
    $("metrics").innerHTML =
      metric("Total leads", s.total) +
      metric("Today", s.today) +
      metric("This week", s.this_week) +
      metric("Pending geocodes", s.pending_geocodes) +
      metric("JIRA pending", s.jira_pending) +
      metric("Emails pending", s.email_pending);
    breakdown("by-source", s.by_source);
    breakdown("by-campaign", s.by_campaign);
  }

  function renderMap(leads) {
    var geo = leads.filter(function (l) { return l.latitude != null && l.longitude != null; });
    var map = L.map("map");
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
    if (!geo.length) {
      map.setView([34.5646, -92.5868], 11); // Benton, AR default
      return;
    }
    var bounds = [];
    geo.forEach(function (l) {
      bounds.push([l.latitude, l.longitude]);
      L.circleMarker([l.latitude, l.longitude], {
        radius: 8, fillColor: "#809948", color: "#000000", weight: 1, opacity: 1, fillOpacity: 0.8
      }).addTo(map).bindPopup(
        '<a href="#" onclick="window.__leadDetail(' + l.id + ');return false;">' +
        esc(l.first_name + " " + l.last_name) + "</a><br>" + esc(l.full_address)
      );
    });
    if (bounds.length === 1) { map.setView(bounds[0], 15); } else { map.fitBounds(bounds); }
  }

  function renderTable(leads) {
    $("leads-tbody").innerHTML = leads.map(function (l) {
      return '<tr data-lead="' + esc(l.id) + '"' +
        ' onclick="window.__leadDetail(' + l.id + ')">' +
        "<td>" + esc(l.first_name + " " + l.last_name) + "</td>" +
        "<td>" + esc(l.email) + "</td>" +
        "<td>" + esc(l.full_address) + "</td>" +
        "<td>" + esc(l.source || "-") + "</td>" +
        "<td>" + esc(l.geocode_status) + "</td>" +
        "<td>" + esc((l.created_at || "").replace("T", " ").slice(0, 16)) + "</td>" +
        "</tr>";
    }).join("");
  }

  function renderAudit(events) {
    $("audit-tbody").innerHTML = (events || []).map(function (e) {
      return "<tr><td>" + esc(e.event_type) + "</td><td>" + esc(e.actor || "-") +
        "</td><td>" + esc(e.path || "") + "</td><td>" +
        esc((e.created_at || "").replace("T", " ").slice(0, 19)) + "</td></tr>";
    }).join("") || '<tr><td colspan="4" class="muted">No admin activity recorded yet.</td></tr>';
  }

  window.__leadDetail = function (id) {
    api("/admin/api/lead/" + id).then(function (l) {
      var c = l.consent || {}, sig = l.signature || {};
      $("detail-body").innerHTML =
        "<p><b>" + esc(l.first_name + " " + l.last_name) + "</b> — " + esc(l.email) +
        (l.phone ? " · " + esc(l.phone) : "") + "</p>" +
        "<p>" + esc(l.full_address) + "</p>" +
        "<p class='muted'>Consent v" + esc(c.version || "?") + " on " + esc(c.accepted_at || "?") +
        " · signed as “" + esc(sig.full_name_typed || "?") + "” (waiver " + esc(sig.waiver_version || "?") + ")</p>" +
        (l.notes ? "<p>" + esc(l.notes) + "</p>" : "") +
        '<p><a class="btn" href="' + API + "/admin/lead/" + l.id + '/pdf" target="_blank" rel="noopener">Download PDF consent form</a></p>';
      $("detail").classList.add("open");
      $("detail").scrollIntoView({ behavior: "smooth" });
    }).catch(function (e) { fail("lead detail: " + e.message); });
  };

  function boot() {
    if (!API) { fail("ADMIN_API_BASE is not configured (config.js)"); return; }
    ["csv", "geojson", "kml"].forEach(function (kind) {
      $("exp-" + kind).href = API + "/export/" + kind;
      $("exp-" + kind).target = "_blank";
      $("exp-" + kind).rel = "noopener";
    });
    Promise.all([api("/admin/api/summary"), api("/admin/api/leads")])
      .then(function (results) {
        var summary = results[0], leads = results[1].leads;
        renderSummary(summary);
        renderMap(leads);
        renderTable(leads);
        $("loading").style.display = "none";
        $("dash").style.display = "block";
        return api("/admin/api/audit").then(renderAudit).catch(function () {
          renderAudit([]);
        });
      })
      .catch(function (e) { fail(e.message); });
  }

  document.addEventListener("DOMContentLoaded", boot);
})();
