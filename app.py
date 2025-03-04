from flask import Flask, request, render_template_string
import pandas as pd

app = Flask(__name__)


def assign_championship_points(sorted_dogs):
    num_dogs = len(sorted_dogs)
    points_map = {
        range(3, 7): [2, 1, 0, 0, 0],
        range(7, 10): [3, 2, 1, 0, 0],
        range(10, 20): [4, 3, 2, 1, 0],
        range(20, 1000): [5, 4, 3, 2, 1]
    }

    points = [0] * len(sorted_dogs)

    for r, p_list in points_map.items():
        if num_dogs in r:
            for i in range(min(5, num_dogs)):
                points[i] = p_list[i]
            break

    return points


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    error_message = None
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file, skiprows=1)
                elif file.filename.endswith('.xlsx'):
                    df = pd.read_excel(file, skiprows=1, engine='openpyxl')
                else:
                    raise ValueError(
                        "Unsupported file format. Please upload a CSV or XLSX file.")

                required_columns = {'Placement', 'Highest Title', 'Dog Name',
                                    'Registration Number', 'Score', 'Course', 'Stock', 'HIT Points'}
                nq_dogs = df[df['Score'].str.contains('NQ', na=False)]
                df['Score'] = pd.to_numeric(df['Score'], errors='coerce')
                df = df.dropna(subset=['Score'])
                df = df[list(required_columns)].sort_values(
                    by=['Score'], ascending=False)
                unique_dogs = df.drop_duplicates(
                    subset=['Dog Name'], keep='first')
                duplicate_dogs = df[df.duplicated(
                    subset=['Dog Name'], keep='first')]
                unique_dogs['HIT Points'] = assign_championship_points(
                    unique_dogs)
                unique_dogs['Placement'] = [i+1 if i <
                                            5 else '-' for i in range(len(unique_dogs))]
                duplicate_dogs['HIT Points'] = '-'
                duplicate_dogs['Placement'] = '-'

                hx_dogs = unique_dogs[unique_dogs['Highest Title'] == 'HX']
                hc2_plus_dogs = unique_dogs[unique_dogs['Highest Title'].str.startswith(
                    'HC') & ~unique_dogs['Highest Title'].eq('HC')]
                additional_lists = []
                filtered_dogs = unique_dogs

                for _, hx_dog in hx_dogs.iterrows():
                    hc2_plus_dogs = filtered_dogs[filtered_dogs['Highest Title'].str.startswith(
                        'HC') & ~filtered_dogs['Highest Title'].eq('HC')]
                    defeated_by_hc2_plus = hc2_plus_dogs[hc2_plus_dogs['Score']
                                                         > hx_dog['Score']]
                    if not defeated_by_hc2_plus.empty:
                        filtered_dogs = filtered_dogs[~filtered_dogs['Dog Name'].isin(
                            defeated_by_hc2_plus['Dog Name'])].copy()
                        filtered_dogs = filtered_dogs.sort_values(
                            by=['Score'], ascending=False)
                        if hx_dog['Dog Name'] in filtered_dogs.head(5)['Dog Name'].values:
                            filtered_dogs['Placement'] = [
                                i+1 if i < 5 else '-' for i in range(len(filtered_dogs))]
                            filtered_dogs['HIT Points'] = assign_championship_points(
                                filtered_dogs)
                            additional_lists.append(filtered_dogs)
                        else:
                            pass

                column_order = ['Placement', 'Highest Title', 'Dog Name',
                                'Registration Number', 'Score', 'Course', 'Stock', 'HIT Points']
                unique_dogs = unique_dogs[column_order]
                duplicate_dogs = duplicate_dogs[column_order]

                for i in range(len(additional_lists)):
                    additional_lists[i] = additional_lists[i][column_order]

                return render_template_string('''
                <!doctype html>
                <html>
                <head>
                    <title>Championship Points Record</title>
                    <style>
                        body { font-family: 'Roboto Slab', sans-serif; text-align: center; margin: 50px; background-color: #f8f9fa; }
                        table { width: 80%; margin: auto; border-collapse: collapse; }
                        th, td { border: 1px solid black; padding: 10px; }
                        th { background-color: #834610; color: white; text-align: center; }

                        table { margin-bottom: 30px; }


                        /* Updated button & link styles */
                        a, input[type="submit"] {
                            display: inline-block;
                            padding: 10px 20px;
                            background-color: white; /* White inside */
                            color: #834610; /* Text color */
                            border: 2px solid #834610; /* Border color */
                            cursor: pointer;
                            border-radius: 5px;
                            font-weight: bold;
                            text-decoration: none;
                            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); /* Drop shadow */
                            transition: all 0.3s ease-in-out;
                        }

                        a:hover, input[type="submit"]:hover {
                            background-color: #f0e0d6; /* Light beige on hover */
                            box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.3); /* Stronger shadow */
                        }
                    </style>
                </head>
                <body>
                <h1>Championship Points Record Form</h1>
                {% if not unique_dogs.empty %}
                    <div style="display: flex; justify-self: center; justify-content: space-between; width: 60%; align-items: center; margin-left: 50px">
                        <div></div>
                        <h2 style="text-align: center;">Main Competition Results</h2>
                        <a href="/" style="
                            text-decoration: none;
                            color: #834610;
                            background-color: white;
                            padding: 10px 20px;
                            border: 2px solid #834610;
                            border-radius: 5px;
                            font-weight: bold;
                            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
                            transition: all 0.3s ease-in-out;
                            margin-right: -120px;">  <!-- Button stays on the left -->
                            Upload Another File
                        </a>
                    </div>
                                            <table>{{ unique_dogs.to_html(classes='dataframe', index=False) | safe }}</table>
                                        {% endif %}
                                        {% if not duplicate_dogs.empty %}
                                            <h2>Duplicate Dogs</h2>
                                            <table>{{ duplicate_dogs.to_html(classes='dataframe', index=False) | safe }}</table>
                                        {% endif %}
                    {% for additional_list in additional_lists %}
                        <h2>Alternative Rankings Due to HC2+ Removal (List {{ loop.index }})</h2>
                        <table>
                            {{ additional_list.to_html(classes='dataframe', index=False) | safe }}
                        </table>
                    {% endfor %}
                    <br>
                </body>
                </html>
                ''', unique_dogs=unique_dogs, duplicate_dogs=duplicate_dogs, additional_lists=additional_lists)

            except Exception as e:
                error_message = f"Error processing file: {str(e)}"

    return render_template_string('''
    <!doctype html>
    <html>
    <head>
        <img src="{{ url_for('static', filename='logo.png') }}" alt="Championship Logo", style="width:256px;height:256px; vertical-align:middle; margin:0px;">
        <title>Championship Points Record</title>
        <style>
            body { font-family: Roboto Slab, sans-serif; text-align: center; margin: 10px; background-color: #f8f9fa; }
            h1 { margin-top: -30px; } /* Moves the title up */
            form { margin-top: 20px; padding: 20px; background: white; border-radius: 10px; display: inline-block; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1); }
            input[type="file"] { margin-bottom: 10px; }
            /* Style for both upload buttons */
            input[type="submit"], a {
                padding: 10px 20px;
                background-color: white; /* White inside */
                color: #834610; /* Text color */
                border: 2px solid #834610; /* Border color */
                cursor: pointer;
                border-radius: 5px;
                font-weight: bold;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); /* Drop shadow */
                transition: all 0.3s ease-in-out;
            }
            input[type="submit"]:hover { background-color: #FFEFE0; }
            .error { color: red; font-weight: bold; margin-top: 10px; }
        </style>
    </head>
    <body>

        <h1>Championship Points Record Form</h1>
        <form action="/" method="post" enctype="multipart/form-data">
            <input type="file" name="file"><br>
            <input type="submit" value="Upload">
        </form>
        {% if error_message %}
            <p class="error">{{ error_message }}</p>
        {% endif %}


    </body>
    </html>
    ''', error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)
