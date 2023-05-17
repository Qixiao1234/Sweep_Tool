import re
import os
import sys
import time
import xlwt

from lxml import etree


#==========================================Parse==================================================

# {xxx(sla): xxx(jops), Geomean: xxx, Max: xxx}
def parse_specJBB(fpath):
    doc = etree.parse(fpath, parser = etree.HTMLParser(encoding = "utf-8"))
    main_desc = doc.xpath("//div[@class='section mainDesc']//td[2]/a/text()")
    max_jops = re.findall(r": (\d+) .* max-jOPS", main_desc[0])[0]
    results = {"Max": max_jops}
    (cells_sla, cells_jops) = (doc.xpath("//td[@class='txHeader' and "              \
            "text()='Response time percentile is 99-th']/../.."                     \
            "//td[@class='txHeader' and text()='%s']/../td/text()" % i)             \
            for i in ("SLA (us)", "jOPS"))
    assert len(cells_sla) == len(cells_jops)
    for i in range(1, len(cells_sla)):
        results[cells_sla[i]] = cells_jops[i]
    return results


# niteration,
# {<benchmark>: [(copies, run time, rate), ...,
#                (avg copies, avg run time, avg rate)],
#               ...,
#  <base_name>: <value>}
def parse_specCPU(fpath, benchmarks, base_name, avg_only = False):
    fd = open(fpath)
    raw = fd.read()
    fd.close()
    results = {}
    ndup = None
    for name in benchmarks:
        match = re.findall(name + r"\s+(\d+)\s+(\d+)\s+(\d+)", raw)
        if ndup is None:
            ndup = len(match)
        else:
            assert ndup == len(match)
        results[name] = match if not avg_only else match[-1]
    match = re.findall(base_name + r"\s+(\d+)", raw)
    assert len(match) == 1
    results[base_name] = match[0]
    return (ndup - 1, results)


# [power(100%), power(90%), ... power(10%), power(idle)]
def _parse_ptu_power_steps(array):
    powers = [x[1] for x in array]
    dist = sorted(powers)
    i = int(len(dist) * 0.05)
    (lower, upper) = (dist[i], dist[-i])
    del dist
    height = (upper - lower) * 0.75
    width = int(len(array) * 0.01)
    in_group = False
    (in_times, out_times) = ([], [])
    for i in range(width, len(array) - width):
        v = powers[i]
        if not in_group:
            if v > min(powers[i - width: i]) + height:
                in_group = True
                in_times.append(array[i][0])
        else:
            if v > min(powers[i + 1: i + width + 1]) + height:
                in_group = False
                out_times.append(array[i][0])
        if len(out_times) == 4:
            break
    busy_time = sum((out_times[i] - in_times[i] for i in range(4))) / 4
    idle_time = sum((in_times[i + 1] - out_times[i] for i in range(3))) / 3
    period = busy_time + idle_time
    mid_time = (in_times[3] + out_times[3]) / 2
    pick_time = busy_time * 0.4
    (start_time, stop_time) = (mid_time - pick_time, mid_time + pick_time)
    (total, count) = (0, 0)
    results = []
    for (t, v) in array:
        if t >= start_time:
            total += v
            count += 1
        if t >= stop_time:
            results.append(total / count)
            if len(results) == 11:
                return results
            (total, count) = (0, 0)
            start_time += period
            stop_time += period
    raise RuntimeError("No enough power steps parsed")


# {dev_xxx: [power(100%), power(90%), ... power(10%), power(idle)],
#   ...}
def _parse_ptu(fpath, devices):
    fd = open(fpath)
    lines = fd.readlines()
    fd.close()
    splitor = lambda line: [x.strip() for x in line.split(",")]
    def adapt():
        headers = set(("Timestamp", "Device", "Power"))
        for i in range(len(lines)):
            items = splitor(lines[i])
            if headers <= set(items):
                return (items.index("Timestamp"), items.index("Device"),
                        items.index("Power"), i)
        raise RuntimeError("No column named <Timestamp>, <Device> or <Power>")
    (col_timestamp, col_device, col_power, iline) = adapt()
    max_icolumn = max(col_timestamp, col_device, col_power)
    arrays = {}
    for device in devices:
        arrays[device] = []
    for i in range(iline + 1, len(lines)):
        items = splitor(lines[i])
        if len(items) <= max_icolumn:
            break
        (device, power) = (items[col_device], items[col_power])
        if device not in arrays or power == "":
            continue
        (datetime, ms) = items[col_timestamp].split(".")
        timestamp = time.mktime(time.strptime(datetime, "%m/%d/%y %H:%M:%S")) + float("0." + ms)
        arrays[device].append((timestamp, float(power)))
    for device in devices:
        arrays[device] = _parse_ptu_power_steps(arrays[device])
    return arrays


# [(ssj_ops(100%), power(100%)), (ssj_ops(90%), power(90%)), ...
#  (ssj_ops(10%), power(10%)), (ssj_ops(idle), power(idle))]
def parse_specPower(fpath, fpath_ptu, devices = ["CPU0", "CPU1"]):
    results = _parse_ptu(fpath_ptu, devices)
    powers = [0] * 11
    for device in devices:
        array = results[device]
        for i in range(11):
            powers[i] += array[i]
    fd = open(fpath)
    lines = fd.readlines()
    fd.close()
    results = []
    percent = 100
    i = 0
    for line in lines:
        items = line.split("|")
        if len(items) == 5 and items[0].strip() == ("%d%%" % percent):
            value = items[2].replace(",", "").strip()
            results.append((value, powers[i]))
            i += 1
            percent -= 10
            if percent == 0:
                results.append((0, powers[i]))
                break
    assert len(results) == 11
    return results


#============================================Export================================================

class Sheet:

    def __init__(self):
        self._root = {}

    # config: dict {"max_uncore_freq": xxx, "fc1e": xxx, "ai": xxx,
    #       "UP": xxx, "uncore_freq": xxx}
    # iteration: 2D array, row-first table of an iteration result
    def add(self, config, iteration):
        level1 = self._root
        max_uncore_freq = config["max_uncore_freq"]
        if max_uncore_freq not in level1:
            level1[max_uncore_freq] = {}
        level2 = level1[max_uncore_freq]
        fc1e = config["fc1e"]
        if fc1e not in level2:
            level2[fc1e] = {}
        level3 = level2[fc1e]
        ai = config["ai"]
        iterations_key = (config["UP"], config["uncore_freq"]) if ai else "disable"
        if iterations_key not in level3:
            level3[iterations_key] = []
        iterations = level3[iterations_key]
        iterations.append(iteration)

    def export(self, book, sheet_name, row_headers, ncolumn, col_headers):
        if len(self._root) == 0:
            return
        sheet = book.add_sheet(sheet_name)
        iteration_nrow = len(row_headers) - (0 if col_headers is None else 1)
        x = 1
        level1 = self._root
        for max_uncore_freq in level1:
            x1 = x
            level2 = level1[max_uncore_freq]
            for fc1e in level2:
                x2 = x
                level3 = level2[fc1e]
                for iterations_key in level3:
                    x3 = x
                    iterations = level3[iterations_key]
                    for iteration in iterations:
                        assert len(iteration) == iteration_nrow
                        y = 3
                        if col_headers is not None:
                            for i in range(ncolumn):
                                sheet.write(y, x + i, col_headers[i])
                            y += 1
                        for row in iteration:
                            for i in range(ncolumn):
                                sheet.write(y, x + i, row[i])
                            y += 1
                        x += ncolumn
                    sheet.write_merge(2, 2, x3, x - 1,
                            "AI disable" if iterations_key == "disable" else    \
                            "UP = %s & uncore = %s" % iterations_key)
                sheet.write_merge(1, 1, x2, x - 1, "FC1E " + fc1e)
            sheet.write_merge(0, 0, x1, x - 1,
                    "max uncore freq = %.1f GHz" % (float(max_uncore_freq) / 10))
        y = 3
        for h in row_headers:
            sheet.write(y, 0, h)
            y += 1


class SheetSpecJBB(Sheet):

    def __init__(self, slas = ("10000", "25000", "50000", "75000", "100000",
            "Geomean", "Max")):
        super().__init__()
        self._slas = slas

    def add(self, config, fpath):
        results = parse_specJBB(fpath)
        rows = [(results[x],) for x in self._slas]
        super().add(config, rows)

    def export(self, book):
        row_headers = ["SLA (us)", *self._slas]
        return super().export(book, "SpecJBB", row_headers, 1, ["jOPS"])


class SheetSpecCPU(Sheet):

    def __init__(self, benchmarks, base_name):
        super().__init__()
        self._benchmarks = benchmarks
        self._base_name = base_name
        self._niter = 0

    def add(self, config, fpath):
        (niter, results) = parse_specCPU(fpath, self._benchmarks, self._base_name)
        if self._niter == 0:
            self._niter = niter
        elif niter != self._niter:
            raise RuntimeError("SpecInt has different iterations")
        rows = []
        for x in self._benchmarks:
            row_results = results[x]
            row = []
            for i in range(niter):
                row.append(row_results[i][2])   # 2 = Base Rate
            row.append(row_results[-1][2])      # 2 = Base Rate
            rows.append(row)
        row = [""] * niter
        row.append(results[self._base_name])
        rows.append(row)
        super().add(config, rows)

    def export(self, book, sheet_name):
        row_headers = ["Benchmark", *self._benchmarks, self._base_name]
        col_headers = (["Est. Base Rate"] * self._niter) + ["Med"]
        return super().export(book, sheet_name, row_headers, self._niter + 1, col_headers)


class SheetSpecInt(SheetSpecCPU):

    def __init__(self, benchmarks = ("500.perlbench_r", "502.gcc_r", "505.mcf_r",
            "520.omnetpp_r", "523.xalancbmk_r", "525.x264_r", "531.deepsjeng_r",
            "541.leela_r", "548.exchange2_r", "557.xz_r")):
        super().__init__(benchmarks, "int_base")

    def export(self, book):
        return super().export(book, "SIR")


class SheetSpecFp(SheetSpecCPU):

    def __init__(self, benchmarks = ("503.bwaves_r", "507.cactuBSSN_r", "508.namd_r",
            "510.parest_r", "511.povray_r", "519.lbm_r", "521.wrf_r", "526.blender_r",
            "527.cam4_r", "538.imagick_r", "544.nab_r", "549.fotonik3d_r", "554.roms_r")):
        super().__init__(benchmarks, "fp_base")

    def export(self, book):
        return super().export(book, "SFR")


class SheetSpecPower(Sheet):

    def __init__(self):
        super().__init__()

    def add(self, config, fpath, fpath_ptu):
        results = parse_specPower(fpath, fpath_ptu)
        results.reverse()
        super().add(config, results)

    def export(self, book):
        row_headers = ["Utilization", *["%d%%" % i for i in range(0, 101, 10)]]
        col_headers = ["Performance", "Power_All"]
        return super().export(book, "SpecPower", row_headers, 2, col_headers)


class Excel:

    def __init__(self):
        self._sheet_specJBB = SheetSpecJBB()
        self._sheet_specInt = SheetSpecInt()
        self._sheet_specFp = SheetSpecFp()
        self._sheet_specPower = SheetSpecPower()

    def addSpecJBB(self, config, fpath):
        self._sheet_specJBB.add(config, fpath)

    def addSpecInt(self, config, fpath):
        self._sheet_specInt.add(config, fpath)
    
    def addSpecFp(self, config, fpath):
        self._sheet_specFp.add(config, fpath)
    
    def addSpecPower(self, config, fpath, fpath_ptu):
        self._sheet_specPower.add(config, fpath, fpath_ptu)

    def export(self, fpath):
        book = xlwt.Workbook()
        self._sheet_specJBB.export(book)
        self._sheet_specInt.export(book)
        self._sheet_specFp.export(book)
        self._sheet_specPower.export(book)
        book.save(fpath)


#========================================Scan======================================================

def scan_directory(dirpath, export_fpath):
    regx1 = re.compile(r"performance-wl-(\w+)-iter-(\d+)-uC-(\d+)"              \
            "-fc1e-(.+)-ai-disable\.(\w+)")
    regx2 = re.compile(r"performance-wl-(\w+)-iter-(\d+)-uC-(\d+)"              \
            "-uP-(\d+)-uF-(\d+)-fc1e-(.+)-ai-enable\.(\w+)")
    excel = Excel()
    for (dirpath, _, fnames) in os.walk(dirpath):
        for fname in fnames:
            while True:
                items = regx1.findall(fname)
                if len(items) == 1 and len(items[0]) == 5:
                    (workload, _, max_uncore_freq, fc1e, ftype) = items[0]
                    ai = False
                    break
                items = regx2.findall(fname)
                if len(items) == 1 and len(items[0]) == 7:
                    (workload, _, max_uncore_freq, up, uncore_freq, fc1e, ftype) = items[0]
                    ai = True
                    break
                ai = None
                break
            if ai is None:
                continue
            config = {"max_uncore_freq": max_uncore_freq, "fc1e": fc1e, "ai": ai}
            if ai:
                config["uncore_freq"] = uncore_freq
                config["UP"] = up
            fpath = os.path.join(dirpath, fname)
            if workload == "specjbb":
                assert ftype == "html"
                excel.addSpecJBB(config, fpath)
            elif workload == "SIR":
                assert ftype == "txt"
                excel.addSpecInt(config, fpath)
            elif workload == "SFR":
                assert ftype == "txt"
                excel.addSpecFp(config, fpath)
            elif workload == "specpower":
                assert ftype == "txt"
                ptu_fname = "ptu%s_ptumon.csv" % fname[len("perfermance"): -len(ftype) - 1]
                ptu_fpath = os.path.join(dirpath, ptu_fname)
                excel.addSpecPower(config, fpath, ptu_fpath)
    excel.export(export_fpath)


if len(sys.argv) != 3:
    print("USAGE: %s <log_folder> <export_path>" % sys.argv[0])
else:
    (log_folder, export_path) = (sys.argv[1], sys.argv[2])
    scan_directory(log_folder, export_path)