top_part = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="{}static/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" href="{}static/css/view.css">
<link rel="stylesheet" href="{}static/css/magnific-popup.css">
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap" rel="stylesheet">
<script src={}static/js/jquery-3.5.1.min.js></script>
<script src={}static/bootstrap/js/bootstrap.min.js></script>
<script src={}static/js/jquery.magnific-popup.min.js></script>
<script src={}static/js/view.js></script>
</head>
<body>

<a class=fixedatthetop><p>{}</p></a>

<div align=center>
    <br><br>\n\n"""

result_part = """<h5>📋 Link : <a href="https://prnt.sc/{}" target="_blank">{}</a> | Hash : {} 📋</h5>
<br>

    <a class="image-popup-no-margins" href="{}">
        <img src="{}">
    </a>

    <br><br>
    <h5 reference={}>🔍 Found this image <b>1</b> time</h5>

    <div class=detected>
        <h1>Words detected</h1>
        <table class="table">
            <thead class=thead-dark>
                <tr>
                    {}
                </tr>
            </thead>
            <tbody>
                {}
            </tbody>
        </table>
    </div>
    <a class="btn btn-primary buttons" style="margin-right:15px" href="{}" target="_blank">RAW</a>
    <a class="btn btn-primary buttons" href="{}" target="_blank">LINKS</a>
    
    <hr>"""