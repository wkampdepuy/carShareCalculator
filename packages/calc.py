import pandas as pd
import numpy as np



def carshare_calculator(minutes, kilometers, frequency=1):
    # input
    data_df = pd.read_excel("C:/Users/kampw/Desktop/carshare_data_v4.xlsx")
    sixt_packages = pd.read_excel("C:/Users/kampw/Desktop/carshare_data_v4.xlsx", sheet_name='Sixt packages')

    data = data_df.copy()

    # sixt ---------------------------------------------------------------------------------------------------

    # ADD SIXT KILOMETER PACKAGES

    data_sixt = data[data['Service'] == 'Sixt'].copy()

    # calculate overtime fee
    overtime = minutes - data_sixt[(data_sixt.Minutes < minutes) & (data_sixt.Minutes > 0)]["Minutes"]
    overtime_fee = data_sixt.loc[overtime.index]["Overtime fee (per min.)"] * overtime

    # calculate overmilage fee
    data_sixt['Package fee'] = 0
    data_sixt['Overmilage fee'] = 0
    data_sixt['Kilometer package'] = ''

    overmilage = kilometers - \
                 data_sixt[(data_sixt["km's included"] < kilometers) & (data_sixt["Overmilage fee (per km)"] > 0)][
                     "km's included"]

    # iterate over plans with overmilage
    for index, option in data_sixt.loc[overmilage.index, :].iterrows():
        overmilage_fee = option["Overmilage fee (per km)"] * (kilometers - option["km's included"])

        best_pack = ''
        lowest_cost = overmilage_fee

        for pack_price, pack_kms in sixt_packages[['Price', 'Kilometers']].values:
            new_overmilage_fee = option["Overmilage fee (per km)"] * max(0, (
                    kilometers - option["km's included"] - pack_kms))

            if new_overmilage_fee + pack_price < lowest_cost:
                best_pack = "{} km package".format(pack_kms)
                lowest_cost = new_overmilage_fee + pack_price
                data_sixt.at[index, 'Kilometer package'] = best_pack
                data_sixt.at[index, 'Package fee'] = pack_price * frequency
                data_sixt.at[index, 'Overmilage fee'] = new_overmilage_fee * frequency

    # add fees to dataframe
    data_sixt["Overtime fee"] = overtime_fee * frequency
    data_sixt["Kilometer fee"] = data_sixt["Per km"] * kilometers * frequency
    data_sixt["Minute fee"] = data_sixt["Per min."] * minutes * frequency
    data_sixt["Fixed rate"] = data_sixt["Fixed rate"] * frequency

    # total cost
    data_sixt["Total cost"] = data_sixt[
        ["Fixed rate", "Overtime fee", "Overmilage fee", "Package fee", "Kilometer fee", "Minute fee"]].fillna(0).sum(
        axis=1)

    # share-now ---------------------------------------------------------------------------------------------------

    data_sharenow = data[data['Service'] == 'SHARE NOW'].copy()

    # calculate overtime fee
    overtime = minutes - data_sharenow[(data_sharenow.Minutes < minutes) & (data_sharenow.Minutes > 0)]["Minutes"]
    overtime_fee = data_sharenow.loc[overtime.index]["Overtime fee (per min.)"] * overtime

    # calculate overmilage fee
    overmilage = kilometers - \
                 data_sharenow[(data_sharenow["km's included"] < kilometers) & (data_sharenow["km's included"] > 0)][
                     "km's included"]
    overmilage_fee = data_sharenow.loc[overmilage.index]["Overmilage fee (per km)"] * overmilage

    # add fees to dataframe
    data_sharenow["Overtime fee"] = overtime_fee * frequency
    data_sharenow["Overmilage fee"] = overmilage_fee * frequency
    data_sharenow["Kilometer fee"] = data_sharenow["Per km"] * kilometers * frequency
    data_sharenow["Minute fee"] = data_sharenow["Per min."] * minutes * frequency
    data_sharenow["Fixed rate"] = data_sharenow["Fixed rate"] * frequency

    # total cost
    data_sharenow["Total cost"] = data_sharenow[
        ["Fixed rate", "Overtime fee", "Overmilage fee", "Kilometer fee", "Minute fee", "Monthly cost"]].fillna(0).sum(
        axis=1)

    # mywheels ---------------------------------------------------------------------------------------------------

    data_mywheels = data[data['Service'] == 'MyWheels'].copy()

    # discount after 2 days (25%)
    if minutes > 24 * 2 * 60:
        # max 10 times hourly rate per day
        data_mywheels["Kilometer fee"] = data_mywheels["Per km"] * kilometers * frequency
        data_mywheels["Minute fee"] = (divmod(minutes / 60, 24)[0] * data_mywheels["Per min."] * 60 * 10 +
                                       divmod(minutes / 60, 24)[1] * data_mywheels["Per min."] * 60) * frequency
        data_mywheels["Discount"] = -0.25 * data_mywheels[['Kilometer fee', 'Minute fee']].sum(axis=1)

    else:
        data_mywheels["Kilometer fee"] = data_mywheels["Per km"] * kilometers * frequency
        data_mywheels["Minute fee"] = (divmod(minutes / 60, 24)[0] * data_mywheels["Per min."] * 60 * 10 +
                                       divmod(minutes / 60, 24)[1] * data_mywheels["Per min."] * 60) * frequency
        data_mywheels["Discount"] = -data_mywheels["Trip discount"] * data_mywheels[
            ['Kilometer fee', 'Minute fee']].sum(axis=1)

    data_mywheels['Total cost'] = data_mywheels[['Kilometer fee', 'Minute fee', 'Discount', 'Monthly cost']].fillna(
        0).sum(axis=1)

    # greenwheels ---------------------------------------------------------------------------------------------------

    data_greenwheels = data[data['Service'] == 'Greenwheels'].copy()

    # calculate overtime fee
    overtime = minutes - data_greenwheels[(data_greenwheels.Minutes < minutes) & (data_greenwheels.Minutes > 0)][
        "Minutes"]
    data_greenwheels["Overtime"] = overtime
    overtime_fee = np.maximum((data_greenwheels[data_greenwheels["Overtime"] > 0]["Overtime"] *
                               data_greenwheels[data_greenwheels["Overtime"] > 0]["Overtime fee (per min.)"]), 25)
    data_greenwheels["Overtime fee"] = overtime_fee

    # total cost
    data_greenwheels["Overtime fee"] = overtime_fee * frequency
    data_greenwheels["Kilometer fee"] = data_greenwheels["Per km"] * kilometers * frequency
    data_greenwheels["Minute fee"] = data_greenwheels["Per min."] * minutes * frequency
    data_greenwheels["Fixed rate"] = data_greenwheels["Fixed rate"] * frequency

    data_greenwheels['Total cost'] = data_greenwheels[
        ['Overtime fee', 'Kilometer fee', 'Minute fee', 'Fixed rate', 'Monthly cost']].sum(axis=1)

    # total ----------------------------------------------------------------------------------------------------------

    out = pd.concat([data_sixt, data_greenwheels, data_mywheels, data_sharenow]).fillna(0)

    return out


temp = carshare_calculator(10000,100,1).sort_values('Total cost').iloc[0,:]
