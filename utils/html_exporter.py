import json
import os
from datetime import datetime

class HTMLExporter:
    def __init__(self):
        # 1. ĐỌC FILE CHART.JS LOCAL ĐỂ NHÚNG OFFLINE
        self.chart_js_content = ""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            chart_path = os.path.join(current_dir, "chart.umd.min.js")
            with open(chart_path, "r", encoding="utf-8") as f:
                self.chart_js_content = f.read()
            script_tag = f"<script>\n{self.chart_js_content}\n</script>"
        except Exception as e:
            print(f"Không tìm thấy chart.umd.min.js local, chuyển sang dùng CDN: {e}")
            script_tag = "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>"

        # Nối chuỗi để tránh lỗi format ngoặc nhọn của CSS/JS
        self.head_template = """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset='UTF-8'>
        """ + script_tag + """
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
            
            html_content += f"<h2 onclick=\"toggleContent('tc_{idx}')\">{test_name} {status_text}</h2>"
            html_content += f"<div id='tc_{idx}'>" 
            
            # Khối Biểu đồ Chart.js
            labels = json.dumps(detail['chart_labels'])
            data_result = json.dumps(detail['chart_data'])
            data_limit = json.dumps(detail['chart_limit'])
            data_volt = json.dumps(detail['chart_volt']) 
            data_curr = json.dumps(detail['chart_curr']) 
            
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
                            borderColor: '#3B82F6', 
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.1,
                            yAxisID: 'y'
                        }},
                        {{
                            label: 'Max Power Limit',
                            data: {data_limit},
                            borderColor: '#EF4444', 
                            borderDash: [8,4],
                            pointRadius: 0,
                            borderWidth: 2,
                            fill: false,
                            yAxisID: 'y'
                        }},
                        {{
                            label: 'Voltage (V)',
                            data: {data_volt},
                            borderColor: '#10B981', 
                            fill: false,
                            tension: 0.1,
                            yAxisID: 'y1'
                        }},
                        {{
                            label: 'Current (A)',
                            data: {data_curr},
                            borderColor: '#F59E0B', 
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
                            grid: {{ drawOnChartArea: false }}, 
                            min: 0,             
                            suggestedMax: 100
                        }}
                    }}
                }}
            }});
            </script>
            """

            # BẢNG SỐ LIỆU CHI TIẾT (Đã cập nhật STT nội bộ và Cột Kênh)
            html_content += """
            <table>
                <tr>
                    <th>STT</th><th>THỜI GIAN</th><th>THỜI GIAN ĐO (s)</th><th>KÊNH (CH)</th>
                    <th>ĐIỆN ÁP (V)</th><th>DÒNG ĐIỆN (A)</th>
                    <th>CÔNG SUẤT (W)</th><th>P TRUNG BÌNH (W)</th><th>ĐÁNH GIÁ</th>
                </tr>
            """
            
            # Sử dụng enumerate để đánh lại số STT từ 1 cho từng bảng
            for local_stt, row in enumerate(detail['table_data'], start=1):
                # row format: (stt_global, sys_time, elapsed, channel, u, i, p, p_avg, status)
                row_class = "pass-text" if row[8] == "PASS" else "fail-text"
                html_content += f"""
                <tr>
                    <td>{local_stt}</td>
                    <td>{row[1]}</td>
                    <td>{row[2]}</td>
                    <td><b>{row[3]}</b></td>
                    <td>{row[4]}</td>
                    <td>{row[5]}</td>
                    <td>{row[6]}</td>
                    <td>{row[7]}</td>
                    <td class='{row_class}'>{row[8]}</td>
                </tr>
                """
            
            html_content += "</table>"
            html_content += "</div>" 
            html_content += "<div style='text-align:right;margin-top:5px;'><a href='#summary'>↑ Back to Summary</a></div>"

        html_content += self.foot_template

        # Lưu file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return True