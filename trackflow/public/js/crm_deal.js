frappe.ui.form.on('CRM Deal', {
    refresh: function(frm) {
        // Add TrackFlow attribution section
        if (!frm.is_new()) {
            add_attribution_section(frm);
            
            // Show attribution report button for won deals
            if (frm.doc.stage === 'Won' && frm.doc.trackflow_marketing_influenced) {
                frm.add_custom_button(__('View Attribution Report'), function() {
                    show_attribution_report(frm);
                }, __('TrackFlow'));
            }
            
            // Show ROI calculation button
            if (frm.doc.annual_revenue && frm.doc.trackflow_marketing_influenced) {
                frm.add_custom_button(__('Calculate ROI'), function() {
                    calculate_deal_roi(frm);
                }, __('TrackFlow'));
            }
        }
        
        // Add attribution model selector
        add_attribution_model_field(frm);
    },
    
    stage: function(frm) {
        // Trigger attribution calculation when deal is won
        if (frm.doc.stage === 'Won' && frm.doc.trackflow_marketing_influenced) {
            frappe.confirm(
                __('Calculate multi-touch attribution for this deal?'),
                function() {
                    calculate_attribution(frm);
                }
            );
        }
    },
    
    annual_revenue: function(frm) {
        // Update ROI preview
        if (frm.doc.annual_revenue && frm.doc.trackflow_marketing_influenced) {
            update_roi_preview(frm);
        }
    }
});

function add_attribution_section(frm) {
    // Create HTML section for attribution visualization
    let attribution_html = `
        <div class="attribution-section">
            <h4>Marketing Attribution</h4>
            <div class="row">
                <div class="col-md-4">
                    <div class="attribution-metric">
                        <label>First Touch Source</label>
                        <div class="metric-value">${frm.doc.trackflow_first_touch_source || 'None'}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="attribution-metric">
                        <label>Last Touch Source</label>
                        <div class="metric-value">${frm.doc.trackflow_last_touch_source || 'None'}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="attribution-metric">
                        <label>Marketing Influenced</label>
                        <div class="metric-value">${frm.doc.trackflow_marketing_influenced ? 'Yes' : 'No'}</div>
                    </div>
                </div>
            </div>
            <div id="attribution-chart-${frm.doc.name}" class="attribution-chart"></div>
        </div>
    `;
    
    // Add to form
    if (!frm.fields_dict.attribution_html) {
        frm.add_field({
            fieldname: 'attribution_html',
            fieldtype: 'HTML',
            label: 'Attribution',
            options: attribution_html
        });
    } else {
        frm.fields_dict.attribution_html.$wrapper.html(attribution_html);
    }
    
    // Load attribution data if available
    if (frm.doc.trackflow_attribution_data) {
        render_attribution_chart(frm);
    }
}

function add_attribution_model_field(frm) {
    // Add dropdown for attribution model selection
    if (!frm.fields_dict.trackflow_attribution_model) {
        frm.add_field({
            fieldname: 'trackflow_attribution_model',
            fieldtype: 'Select',
            label: 'Attribution Model',
            options: 'Last Touch\nFirst Touch\nLinear\nTime Decay\nPosition Based\nData Driven',
            default: 'Last Touch'
        });
    }
}

function calculate_attribution(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_deal.calculate_attribution',
        args: {
            doc: frm.doc,
            method: null
        },
        callback: function(r) {
            if (r.message) {
                frappe.msgprint(__('Attribution calculated successfully'));
                frm.reload_doc();
            }
        }
    });
}

function show_attribution_report(frm) {
    frappe.call({
        method: 'trackflow.integrations.crm_deal.get_deal_attribution_report',
        args: {
            deal_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                show_attribution_dialog(r.message);
            }
        }
    });
}

function show_attribution_dialog(report_data) {
    let dialog_html = build_attribution_report_html(report_data);
    
    let d = new frappe.ui.Dialog({
        title: __('Deal Attribution Report'),
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'report_html',
            options: dialog_html
        }],
        size: 'extra-large',
        primary_action_label: __('Download Report'),
        primary_action: function() {
            download_attribution_report(report_data);
        }
    });
    
    d.show();
    
    // Render charts after dialog is shown
    setTimeout(function() {
        render_report_charts(report_data);
    }, 100);
}

function build_attribution_report_html(data) {
    let touchpoints_html = '';
    
    if (data.attribution_details && data.attribution_details.touchpoints) {
        data.attribution_details.touchpoints.forEach(function(tp) {
            touchpoints_html += `
                <tr>
                    <td>${tp.timestamp}</td>
                    <td>${tp.type}</td>
                    <td>${tp.source || 'Direct'}</td>
                    <td>${tp.medium || 'None'}</td>
                    <td>${tp.campaign || 'None'}</td>
                    <td>${tp.credit}%</td>
                    <td>${format_currency((tp.credit / 100) * data.value)}</td>
                </tr>
            `;
        });
    }
    
    return `
        <div class="attribution-report">
            <div class="report-summary">
                <h4>Deal Summary</h4>
                <p><strong>Deal Value:</strong> ${format_currency(data.value)}</p>
                <p><strong>Attribution Model:</strong> ${data.attribution_model}</p>
                <p><strong>Marketing Influenced:</strong> ${data.marketing_influenced ? 'Yes' : 'No'}</p>
            </div>
            
            <div class="touchpoint-analysis">
                <h4>Touchpoint Analysis</h4>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Type</th>
                            <th>Source</th>
                            <th>Medium</th>
                            <th>Campaign</th>
                            <th>Credit %</th>
                            <th>Revenue</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${touchpoints_html}
                    </tbody>
                </table>
            </div>
            
            <div class="customer-journey">
                <h4>Customer Journey</h4>
                <div id="journey-timeline"></div>
            </div>
            
            <div class="attribution-visualization">
                <h4>Attribution Distribution</h4>
                <div id="attribution-pie-chart"></div>
            </div>
        </div>
    `;
}

function calculate_deal_roi(frm) {
    // Get campaign costs and calculate ROI
    frappe.call({
        method: 'trackflow.api.analytics.get_deal_roi',
        args: {
            deal_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                show_roi_dialog(r.message);
            }
        }
    });
}

function update_roi_preview(frm) {
    // Show quick ROI preview
    if (frm.doc.annual_revenue) {
        let roi_html = `
            <div class="roi-preview alert alert-info">
                <strong>Potential Revenue:</strong> ${format_currency(frm.doc.annual_revenue)}
                ${frm.doc.trackflow_marketing_influenced ? 
                    '<br><small>This deal is marketing influenced</small>' : ''}
            </div>
        `;
        
        frm.set_df_property('annual_revenue', 'description', roi_html);
    }
}

function render_attribution_chart(frm) {
    // Parse and render attribution data as chart
    try {
        let attribution_data = JSON.parse(frm.doc.trackflow_attribution_data);
        
        if (attribution_data.touchpoints && attribution_data.touchpoints.length > 0) {
            // Prepare data for chart
            let chart_data = attribution_data.touchpoints.map(tp => ({
                name: tp.source || 'Direct',
                value: tp.credit
            }));
            
            // Render donut chart
            new frappe.Chart(`#attribution-chart-${frm.doc.name}`, {
                data: {
                    labels: chart_data.map(d => d.name),
                    datasets: [{
                        values: chart_data.map(d => d.value)
                    }]
                },
                type: 'donut',
                height: 250,
                colors: ['#4299E1', '#48BB78', '#F56565', '#ED8936', '#9F7AEA']
            });
        }
    } catch (e) {
        console.error('Error rendering attribution chart:', e);
    }
}

function render_report_charts(report_data) {
    // Render timeline chart
    if (report_data.customer_journey && report_data.customer_journey.length > 0) {
        let timeline_data = report_data.customer_journey.map((event, idx) => ({
            x: new Date(event.timestamp),
            y: idx + 1,
            label: event.event_type
        }));
        
        new frappe.Chart('#journey-timeline', {
            data: {
                datasets: [{
                    values: timeline_data
                }]
            },
            type: 'line',
            height: 200,
            axisOptions: {
                xAxisMode: 'timeseries'
            }
        });
    }
    
    // Render attribution pie chart
    if (report_data.attribution_details && report_data.attribution_details.touchpoints) {
        let pie_data = {};
        
        report_data.attribution_details.touchpoints.forEach(tp => {
            let key = tp.source || 'Direct';
            pie_data[key] = (pie_data[key] || 0) + tp.credit;
        });
        
        new frappe.Chart('#attribution-pie-chart', {
            data: {
                labels: Object.keys(pie_data),
                datasets: [{
                    values: Object.values(pie_data)
                }]
            },
            type: 'pie',
            height: 300,
            colors: ['#4299E1', '#48BB78', '#F56565', '#ED8936', '#9F7AEA', '#667EEA']
        });
    }
}

function show_roi_dialog(roi_data) {
    let roi_html = `
        <div class="roi-analysis">
            <h4>ROI Analysis</h4>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Deal Value:</strong> ${format_currency(roi_data.deal_value)}</p>
                    <p><strong>Campaign Cost:</strong> ${format_currency(roi_data.campaign_cost)}</p>
                    <p><strong>Net Revenue:</strong> ${format_currency(roi_data.net_revenue)}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>ROI:</strong> ${roi_data.roi}%</p>
                    <p><strong>Campaign:</strong> ${roi_data.campaign || 'Multiple'}</p>
                    <p><strong>Attribution Model:</strong> ${roi_data.attribution_model}</p>
                </div>
            </div>
        </div>
    `;
    
    frappe.msgprint({
        title: __('Deal ROI Analysis'),
        message: roi_html,
        indicator: 'green'
    });
}

function download_attribution_report(report_data) {
    // Generate and download PDF report
    frappe.call({
        method: 'trackflow.api.reports.generate_attribution_pdf',
        args: {
            report_data: report_data
        },
        callback: function(r) {
            if (r.message) {
                window.open(r.message);
            }
        }
    });
}

function format_currency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount || 0);
}

// Add custom CSS
frappe.ui.form.on('CRM Deal', {
    onload_post_render: function(frm) {
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .attribution-section {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 15px 0;
                }
                .attribution-metric {
                    text-align: center;
                    padding: 15px;
                    background: white;
                    border-radius: 5px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .metric-value {
                    font-size: 20px;
                    font-weight: bold;
                    color: #2563eb;
                }
                .attribution-chart {
                    margin-top: 20px;
                }
                .roi-preview {
                    margin-top: 10px;
                }
                .attribution-report {
                    padding: 20px;
                }
                .report-summary {
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .touchpoint-analysis {
                    margin: 20px 0;
                }
                .roi-analysis {
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 5px;
                }
            `)
            .appendTo('head');
    }
});
