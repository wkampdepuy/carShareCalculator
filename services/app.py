from flask import Flask, render_template, request
from calc import carshare_calculator

app = Flask(__name__)

output_columns = ['Service', 'Subscription', 'Plan', 'Car type', 'Kilometer fee', 'Minute fee', 'Fixed rate',
                  'Overtime fee', 'Overmilage fee', 'Package fee', 'Monthly cost', 'Discount', 'Total cost']


@app.route('/', methods=['POST', 'GET'])
def my_form_post():
    if request.method == 'POST':
        kms = request.form['kilometers']
        mins = request.form['duration']
        freq = request.form['frequency']
        carshare_options = carshare_calculator(int(mins), int(kms), int(freq)).sort_values('Total cost')
        carshare_options = carshare_options[output_columns]
        carshare_options.columns = carshare_options.columns.str.replace(' ', '_')

        return render_template('..templates/index.html', kilometers=kms, minutes=mins, frequency=freq,
                               table=[carshare_options.to_html(classes='data')],
                               titles=carshare_options.columns.values)
    else:
        return render_template('..templates/index.html', options='blank')


if __name__ == '__main__':
    app.run()
