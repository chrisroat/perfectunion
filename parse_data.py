import csv

from us import states

# \copy comment_data(id,state_fips,district_fips,name,city,comment) FROM '../icloud.nosync/fcc/perfectunion.csv' WITH (FORMAT csv);


infile = "../icloud.nosync/fcc/unknown_addr_cmt_long.csv"
outfile = "../icloud.nosync/fcc/perfectunion.csv"

zipinfo = "data/natl_zccd_delim.txt"

ZIP2FIPS = {}

with open(zipinfo) as f:
    data = f.readlines()
    for row in data[2:]:
        row = row.strip()
        if not row:
            continue
        state, zipcode, district = row.split(",")
        ZIP2FIPS[zipcode.zfill(5)] = state.zfill(2), district.zfill(2)


zero_zip = 0
no_fips = 0
bad_state = 0

with open(infile) as fin, open(outfile, "w") as fout:
    reader = csv.DictReader(fin)
    writer = csv.writer(fout)

    num_rows = 0
    for row in reader:
        num_rows += 1
        if not num_rows % 20000:
            print(num_rows)

        state = row["state"]
        state_lookup = states.lookup(state)

        if state_lookup in [
            states.AK,
            states.DC,
            states.DE,
            states.MT,
            states.ND,
            states.PR,
            states.SD,
            states.VT,
            states.WY,
        ]:
            state_fips, district_fips = state_lookup.fips, "00"
        else:
            zip_code = row["zip_code"].zfill(5)
            if zip_code == "00000":
                zero_zip += 1
                continue

            fips = ZIP2FIPS.get(zip_code)
            if fips:
                state_fips, district_fips = fips
            else:
                no_fips += 1
                continue

        state_fips_lookup = states.lookup(state_fips)
        if state_lookup != state_fips_lookup:
            bad_state += 1
            continue

        unique_id = int(row["id"])
        name = row["filers"].split(" ")[0]
        city = row["city"]
        comment = row["comment"]
        writer.writerow([unique_id, state_fips, district_fips, name, city, comment])
print((zero_zip, no_fips, bad_state))
