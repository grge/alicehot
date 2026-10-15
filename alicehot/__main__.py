from . import data, hotdays, style

style.apply()
df = data.load_tmax()

hotdays.plot(df, 35, "Alice Springs gets three more weeks of 35 °C days than it used to",
             "days-35")
hotdays.plot(df, 40, "40 °C days in Alice Springs have more than doubled", "days-40")
