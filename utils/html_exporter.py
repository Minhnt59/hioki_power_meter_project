import json
import os
from datetime import datetime

class HTMLExporter:
    def __init__(self):
        # Giữ nguyên CSS và JS từ mẫu của bạn
        self.head_template = """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset='UTF-8'>
        <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
        <style>
        body { font-family: Arial, sans-serif; font-size: 14px; margin: 20px; }
        h2 { background-color: #f2f2f2; padding: 8px; border: 1px solid #ccc; cursor: pointer; margin-top: 25px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 15px; }
        th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: center; }
        th { background-color: #e2e2e2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .info-table { width: auto; min-width: 500px; display: inline-table; }
        .info-table th { text-align: left; padding-right: 20px; }
        .pass-text { color: green; font-weight: bold; }
        .fail-text { color: red; font-weight: bold; }
        </style>
        <script>
        function toggleContent(id) {
            var obj = document.getElementById(id);
            if(obj.style.display === 'none') obj.style.display = 'block';
            else obj.style.display = 'none';
        }
        </script>
        </head>
        <body>
        """
        self.foot_template = "</body></html>"

    def export_report(self, file_path, general_info, summary_data, detailed_data):
        """
        Hàm chính để render file HTML
        """
        html_content = self.head_template

        # 1. THÔNG TIN CHUNG (General Information)
        title = general_info.get("Serial Number", "UNKNOWN")
        html_content += f"<h2 id='top'>THÔNG TIN ĐO KIỂM: {title}</h2>"
        html_content += "<table class='info-table'>"
        
        for key, value in general_info.items():
            if key == "Overall Result":
                css_class = "pass-text" if value.upper() == "PASS" else "fail-text"
                html_content += f"<tr><th>{key}</th><td class='{css_class}'>{value}</td></tr>"
            else:
                html_content += f"<tr><th>{key}</th><td>{value}</td></tr>"
        html_content += "</table>"

        # 2. TÓM TẮT KẾT QUẢ (Summary Table)
        html_content += "<h2 id='summary'>TÓM TẮT KẾT QUẢ</h2>"
        html_content += """
        <table border='1' cellspacing='0' cellpadding='5'>
            <tr style='background:#D9EAD3'>
                <th>STT</th>
                <th>TÊN BÀI ĐO</th>
                <th>SỐ MẪU</th>
                <th>PASS</th>
                <th>FAIL</th>
                <th>LIMIT POWER(W)</th>
                <th>AVERAGE POWER (W)</th>
                <th>VERDICT</th>
            </tr>
        """
        for idx, row in enumerate(summary_data, start=1):
            verdict_class = "pass-text" if row['verdict'].upper() == "PASS" else "fail-text"
            html_content += f"""
            <tr>
                <td>{idx}</td>
                <td><a href='#tc_{idx}'>{row['test_name']}</a></td>
                <td>{row['total']}</td>
                <td>{row['pass_count']}</td>
                <td>{row['fail_count']}</td>
                <td>{row['max_power']}</td>
                <td>{row['final_p_avg']}</td>
                <td class='{verdict_class}'>{row['verdict']}</td>
            </tr>
            """
        html_content += "</table><br/>"

        # 3. KẾT QUẢ CHI TIẾT & ĐỒ THỊ (Detailed Results & Charts)
        html_content += "<h2>KẾT QUẢ ĐO KIỂM CHI TIẾT: </h2>"
        
        for idx, detail in enumerate(detailed_data, start=1):
            test_name = detail['test_name']
            total = detail['total']
            fail_count = detail['fail_count']
            status_text = f"<span class='fail-text'>Fail = {fail_count}/{total}</span>" if fail_count > 0 else f"<span class='pass-text'>Pass = {total}/{total}</span>"
            
            # Header click để collapse
            html_content += f"<h2 onclick=\"toggleContent('tc_{idx}')\">{test_name} {status_text}</h2>"
            html_content += f"<div id='tc_{idx}'>" # Container chứa biểu đồ và bảng
            
            # Khối Biểu đồ Chart.js
            labels = json.dumps(detail['chart_labels'])
            data_result = json.dumps(detail['chart_data'])
            data_limit = json.dumps(detail['chart_limit'])
            data_volt = json.dumps(detail['chart_volt']) # Nhận dữ liệu Voltage
            data_curr = json.dumps(detail['chart_curr']) # Nhận dữ liệu Current
            
            html_content += f"""
            <div style='width:900px;height:350px;margin-bottom:10px;'>
                <canvas id='chart_{idx}'></canvas>
            </div>
            <script>
            new Chart(document.getElementById('chart_{idx}'), {{
                type: 'line',
                data: {{
                    labels: {labels},
                    datasets: [
                        {{
                            label: 'Power (W)',
                            data: {data_result},
                            borderColor: '#3B82F6', // Xanh dương
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.1,
                            yAxisID: 'y'
                        }},
                        {{
                            label: 'Max Power Limit',
                            data: {data_limit},
                            borderColor: '#EF4444', // Đỏ
                            borderDash: [8,4],
                            pointRadius: 0,
                            borderWidth: 2,
                            fill: false,
                            yAxisID: 'y'
                        }},
                        {{
                            label: 'Voltage (V)',
                            data: {data_volt},
                            borderColor: '#10B981', // Xanh lá
                            fill: false,
                            tension: 0.1,
                            yAxisID: 'y1'
                        }},
                        {{
                            label: 'Current (A)',
                            data: {data_curr},
                            borderColor: '#F59E0B', // Cam
                            fill: false,
                            tension: 0.1,
                            yAxisID: 'y1'
                        }}
                    ]
                }},
                options: {{
                    responsive: true, 
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{ 
                        title: {{ display: true, text: '{test_name}' }}, 
                        legend: {{ position: 'top' }} 
                    }},
                    scales: {{ 
                        y: {{ 
                            type: 'linear', 
                            display: true, 
                            position: 'left',
                            title: {{ display: true, text: 'Power (W)' }}
                        }},
                        y1: {{ 
                            type: 'linear', 
                            display: true, 
                            position: 'right',
                            title: {{ display: true, text: 'Voltage (V) / Current (A)' }},
                            grid: {{ drawOnChartArea: false }}, // Ẩn lưới của trục phụ
                            min: 0,             
                            suggestedMax: 100
                        }}
                    }}
                }}
            }});
            </script>
            """

            # Bảng số liệu chi tiết của bài đo
            html_content += """
            <table>
                <tr>
                    <th>STT</th><th>THỜI GIAN</th><th>THỜI GIAN ĐO (s)</th>
                    <th>ĐIỆN ÁP (V)</th><th>DÒNG ĐIỆN (A)</th>
                    <th>CÔNG SUẤT (W)</th><th>P TRUNG BÌNH (W)</th><th>ĐÁNH GIÁ</th>
                </tr>
            """
            for row in detail['table_data']:
                # row format: (stt, sys_time, elapsed, u, i, p, p_avg, status)
                row_class = "pass-text" if row[7] == "PASS" else "fail-text"
                html_content += f"""
                <tr>
                    <td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td>
                    <td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td>
                    <td>{row[6]}</td><td class='{row_class}'>{row[7]}</td>
                </tr>
                """
            
            html_content += "</table>"
            html_content += "</div>" # Đóng div collapse
            html_content += "<div style='text-align:right;margin-top:5px;'><a href='#summary'>↑ Back to Summary</a></div>"

        html_content += self.foot_template

        # Lưu file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return True