"""World Bank Data Indicator API helper.

This is a simple indicator API helper focused on ease of use and getting data
for use with Orange data mining software. For a more comprehensive APIs see
wbpy or wbdata packages.
"""
import urllib
import json
import re
import logging
from collections import defaultdict

from simple_wbd import utils

logger = logging.getLogger(__name__)


class IndicatorDataset(object):
    """Wrapper for indicator dataset.

    This class provides multiple ways of accessing retrieved indicator data.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, api_responses):
        self.api_responses = api_responses

    @staticmethod
    def _get_dates(data):
        """Get all different unique dates from single indicator data.

        Args:
            data (list[dict]): list of indicator data that contains date.

        Returns:
            list[str]: sorted list of all unique date entries.
        """
        return sorted(set(datapoint.get("date") for datapoint in data))

    @staticmethod
    def _parse_value(value):
        """Parse any non empty string value into float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning("Failed to parse fload value.", exc_info=True)

    def _get_data_map(self, data, data_map=None, country_prefix="",
                      date_prefix=""):
        """Get data is a nested dictionary.

        This returns data as a nested default dict, with first level containing
        country data and second level indicator data with dates.

        Note: prefix is useful when aggregating data from multiple indicators.
        usually the prefix can be the indicator itself.

        Args:
            data: Result dict retrieved from world bank data api.
            data_map: Existing data map that will be update with missing data.
                if set to none, a new data_map is created and returned. This
                used for merging data from different indicators.
            country_prefix: Prefix string for all country keys.
            date_prefix: Prefix string for all date keys.

        Returns:
            nested dict containing data grouped by country, indicator and date.
        """
        if data_map is None:
            data_map = defaultdict(lambda: defaultdict(float))
        for datapoint in data:
            country = datapoint.get("country", {}).get("value", "")
            date = datapoint.get("date", "")
            data_map[country_prefix + country][date_prefix + date] = \
                self._parse_value(datapoint.get("value"))
        return data_map

    @staticmethod
    def _get_all_dates(data_map):
        date_set = set()
        for country_data in data_map.values():
            for date in country_data:
                date_set.add(date)

        return sorted(date_set)

    @staticmethod
    def _get_all_countries(data_map):
        return sorted(data_map.keys())

    def _get_single_response_list(self, data):
        """Get list data for a single indicator."""
        headers = ["Country"]
        data_map = self._get_data_map(data)

        all_dates = self._get_all_dates(data_map)
        all_countries = self._get_all_countries(data_map)

        headers.extend(all_dates)
        response = [headers]
        for country in all_countries:
            response.append([country] + [
                data_map[country][date] for date in all_dates
            ])

        return response

    def _get_responses_list(self, response_data):
        """Get list data for multiple indicators."""
        headers = ["Country"]
        data_map = None
        for indicator, indicator_data in response_data.items():
            data_map = self._get_data_map(
                indicator_data,
                data_map=data_map,
                date_prefix=indicator + " - "
            )

        all_dates = self._get_all_dates(data_map)
        all_countries = self._get_all_countries(data_map)

        headers.extend(all_dates)
        response = [headers]
        for country in all_countries:
            response.append([country] + [
                data_map[country][date] for date in all_dates
            ])

        return response

    def as_list(self):
        """Get data as 2D list.

        This function returns data as a 2D list where rows contain country and
        all data related to that country, and columns contain indicator and
        dates.
        """
        if len(self.api_responses) == 1:
            value = next(iter(self.api_responses.values()))
            return self._get_single_response_list(value)

        if len(self.api_responses) > 1:
            return self._get_responses_list(self.api_responses)

        return []


class IndicatorAPI(object):
    """Request data from the World Bank Indicator API."""

    BASE_URL = "http://api.worldbank.org/"
    GET_PARAMS = "?format=json&per_page=100000"
    DEFAULT_COUNTRY_FIELDS = [
        "id",
        "name",
        "incomeLevel_text",
    ]

    _country_field_map = {
        "id": "Id",
        "name": "Name",
        "incomeLevel_text": "Income Level",
    }

    def get_countries(self):
        """Get a list of countries and regions.

        This is a full list of countries and regions that can be used in the
        indicator queries. In the list there are some non ISO codes such as WLD
        for the whole world and other aggregate regions.

        Note that this list does not include all countries (e.g. Israel),
        but only countries that can be queried with the indicator API.

        Returns:
            list[dict]: A list of countries and aggregate regions.
        """
        country_query = "countries" + self.GET_PARAMS
        url = urllib.parse.urljoin(self.BASE_URL, country_query)
        country_result = utils.fetch(url)
        countries = json.loads(country_result)[1]

        dict_to_text = ["region", "adminregion", "incomeLevel", "lendingType"]
        for country in countries:
            for key in dict_to_text:
                country[key + "_text"] = "{value} ({id_})".format(
                    value=country.get(key, {}).get("value"),
                    id_=country.get(key, {}).get("id"),
                )

        return countries

    def get_country_list(self, fields=None, field_map=None):
        """Get list of all available countries."""
        if not field_map:
            field_map = self._country_field_map
        if not fields:
            fields = self.DEFAULT_COUNTRY_FIELDS

        countries = self.get_countries()
        country_list = [[field_map[field] for field in fields]]
        for country in countries:
            country_list.append([country[field] for field in fields])
        return country_list

    @classmethod
    def _filter_indicators(cls, indicators, filter_):

        if filter_.lower() == "featured":
            code_matches = cls._featured
        elif filter_.lower() == "common":
            page = utils.fetch("http://data.worldbank.org/indicator/all")
            codes = re.compile(r"\"([^\"?%`&$ <>=]{3,55})\"")
            code_matches = set(code.lower() for code in codes.findall(page))
        else:
            return indicators

        return [i for i in indicators if i.get("id").lower() in code_matches]

    def get_indicators(self, filter_="Common"):
        """Get a list of indicators.

        Args:
            filter_ (str): Common or Featured. Leave empty for all indicators.

        Returns:
            list[dict]: A list of queryable indicators.
        """
        country_query = "indicators" + self.GET_PARAMS
        url = urllib.parse.urljoin(self.BASE_URL, country_query)
        indicators = json.loads(utils.fetch(url))[1]

        if filter_:
            return self._filter_indicators(indicators, filter_)

        return indicators

    def get_indicator_list(self, filter_="Common"):
        """Get a list of all possible indicators."""
        indicators = self.get_indicators(filter_=filter_)
        indicator_list = [["Id", "Name", "Topics", "Source"]]
        for indicator in indicators:
            indicator_list.append([
                indicator.get("id", "").strip(),
                indicator.get("name", "").strip(),
                ", ".join(
                    topic.get("value", "").strip()
                    for topic in indicator.get("topics", [])
                ),
                indicator.get("source", {}).get("value", "").strip(),
            ])
        return indicator_list

    def _get_countries_map(self):
        """Get a map from country name or code to alpha3 code.

        Returns:
            dict: map of names, alpha2, alpha3 codes to alpha3.
        """
        all_countries = self.get_countries()
        country_map = {c.get("iso2Code"): c.get("id") for c in all_countries}
        country_map.update({c.get("id"): c.get("id") for c in all_countries})
        country_map.update({c.get("name"): c.get("id") for c in all_countries})

        return {k.lower(): v.lower() for k, v in country_map.items() if k}

    def _countries_to_alpha3(self, countries):
        """Filter out invalid countries and return a set of alpha3 codes.

        Args:
            countries (list or str): List of country codes or names, or a
                single country code/name

        Returns:
            set[str]: List of alpha3 country codes for all valid countries.
        """

        if not countries:
            return set()

        if isinstance(countries, str):
            countries = [countries]

        countries = [c.lower() for c in countries if c]

        countries_map = self._get_countries_map()
        alpha3_codes = set()
        for country in countries:
            if country in countries_map:
                alpha3_codes.add(countries_map[country])
            else:
                logger.warning("Ignoring invalid country: %s", country)
        return alpha3_codes

    def _get_indicator_data(self, alpha3_text, indicator):

        query = "countries/{countries}/indicators/{indicator}{params}".format(
            countries=alpha3_text,
            indicator=indicator,
            params="?format=json&per_page=10000",  # lower limit
        )

        url = urllib.parse.urljoin(self.BASE_URL, query)
        header, indicator_data = json.loads(utils.fetch(url))

        # loop through the rest of the pages if they exist
        for page in range(2, header.get("pages", 1) + 1):
            page_url = "{url}&page={page}".format(url=url, page=page)
            indicator_data += json.loads(utils.fetch(page_url))[1]

        return indicator_data

    def get_dataset(self, indicators, countries=None):
        """Get indicator dataset.

        Args:
            indicators (str or list[str]): A single indicator id, or a list of
                requested indicator ids.
            countries (str or list[str]): country id or list of country ids. If
                None, all countries will be used.

        Returns:
            IndicatorDataset: all datasets for the requested indicators.
        """
        if isinstance(indicators, str):
            indicators = [indicators]

        alpha3_codes = self._countries_to_alpha3(countries)
        if alpha3_codes:
            alpha3_text = ";".join(alpha3_codes).upper()
        else:
            alpha3_text = "all"

        indicators_set = set(i.lower() for i in indicators)

        responses = {}
        # pylint: disable=broad-except
        for indicator in indicators_set:
            try:
                responses[indicator] = self._get_indicator_data(
                    alpha3_text, indicator)
            except Exception:
                # We should avoid any errors that can occur due to api
                # responses or invalid data.
                logger.warning(
                    "Failed to fetch indicator: %s", indicator, exc_info=True)

        return IndicatorDataset(responses)

    # Set of featured indicators as of 2016-06-30.
    _featured = frozenset([
        "ag.con.fert.zs",
        "ag.lnd.agri.zs",
        "ag.lnd.arbl.ha.pc",
        "ag.lnd.arbl.zs",
        "ag.lnd.crel.ha",
        "ag.lnd.crop.zs",
        "ag.lnd.el5m.zs",
        "ag.lnd.frst.k2",
        "ag.lnd.frst.zs",
        "ag.lnd.irig.ag.zs",
        "ag.lnd.totl.k2",
        "ag.lnd.trac.zs",
        "ag.prd.crop.xd",
        "ag.prd.food.xd",
        "ag.prd.lvsk.xd",
        "ag.srf.totl.k2",
        "ag.yld.crel.kg",
        "bm.gsr.royl.cd",
        "bn.cab.xoka.cd",
        "bx.grt.exta.cd.wd",
        "bx.grt.tech.cd.wd",
        "bx.gsr.royl.cd",
        "bx.klt.dinv.cd.wd",
        "bx.trf.pwkr.cd.dt",
        "cm.mkt.indx.zg",
        "cm.mkt.lcap.cd",
        "cm.mkt.lcap.gd.zs",
        "cm.mkt.ldom.no",
        "cm.mkt.trad.gd.zs",
        "cm.mkt.trnr",
        "dt.dod.dect.cd",
        "dt.dod.dect.gn.zs",
        "dt.dod.dimf.cd",
        "dt.dod.dpng.cd",
        "dt.dod.dppg.cd",
        "dt.dod.dstc.cd",
        "dt.dod.dstc.ir.zs",
        "dt.dod.mwbg.cd",
        "dt.nfl.dect.cd",
        "dt.oda.odat.cd",
        "dt.oda.odat.gi.zs",
        "dt.oda.odat.gn.zs",
        "dt.oda.odat.mp.zs",
        "dt.oda.odat.pc.zs",
        "dt.oda.odat.xp.zs",
        "dt.tds.dect.ex.zs",
        "eg.egy.prim.pp.kd",
        "eg.elc.accs.zs",
        "eg.elc.rnew.zs",
        "eg.fec.rnew.zs",
        "eg.gdp.puse.ko.pp.kd",
        "eg.imp.cons.zs",
        "eg.nsf.accs.zs",
        "eg.use.comm.cl.zs",
        "eg.use.comm.fo.zs",
        "eg.use.elec.kh.pc",
        "eg.use.pcap.kg.oe",
        "en.atm.co2e.kt",
        "en.atm.co2e.pc",
        "en.atm.ghgt.kt.ce",
        "en.atm.meth.kt.ce",
        "en.atm.noxe.kt.ce",
        "en.atm.pm25.mc.m3",
        "en.atm.pm25.mc.zs",
        "en.bir.thrd.no",
        "en.fsh.thrd.no",
        "en.hpt.thrd.no",
        "en.mam.thrd.no",
        "en.pop.dnst",
        "en.pop.el5m.zs",
        "en.pop.slum.ur.zs",
        "en.urb.lcty.ur.zs",
        "en.urb.mcty.tl.zs",
        "er.h2o.fwtl.k3",
        "er.h2o.fwtl.zs",
        "er.h2o.intr.k3",
        "er.h2o.intr.pc",
        "er.ptd.totl.zs",
        "fb.ast.nper.zs",
        "fb.atm.totl.p5",
        "fb.bnk.capa.zs",
        "fb.cbk.brch.p5",
        "fi.res.totl.cd",
        "fm.lbl.bmny.gd.zs",
        "fm.lbl.bmny.zg",
        "fp.cpi.totl.zg",
        "fr.inr.dpst",
        "fr.inr.lend",
        "fr.inr.lndp",
        "fr.inr.rinr",
        "fr.inr.risk",
        "fs.ast.doms.gd.zs",
        "fs.ast.prvt.gd.zs",
        "gb.xpd.rsdv.gd.zs",
        "gc.bal.cash.gd.zs",
        "gc.dod.totl.gd.zs",
        "gc.rev.xgrt.gd.zs",
        "gc.tax.totl.gd.zs",
        "gc.xpn.totl.gd.zs",
        "ic.bus.disc.xq",
        "ic.bus.ease.xq",
        "ic.bus.nreg",
        "ic.crd.info.xq",
        "ic.elc.time",
        "ic.frm.bkwc.zs",
        "ic.frm.femm.zs",
        "ic.frm.femo.zs",
        "ic.frm.isoc.zs",
        "ic.gov.durs.zs",
        "ic.lgl.cred.xq",
        "ic.reg.durs",
        "ic.reg.proc",
        "ic.tax.totl.cp.zs",
        "ie.ppi.engy.cd",
        "ie.ppi.tele.cd",
        "ie.ppi.tran.cd",
        "ie.ppi.watr.cd",
        "ip.jrn.artc.sc",
        "ip.pat.nres",
        "ip.pat.resd",
        "ip.tmk.nres",
        "ip.tmk.resd",
        "iq.cpa.econ.xq",
        "iq.cpa.irai.xq",
        "iq.cpa.pubs.xq",
        "iq.cpa.soci.xq",
        "iq.cpa.strc.xq",
        "iq.sci.ovrl",
        "is.air.dprt",
        "is.rrs.totl.km",
        "is.shp.good.tu",
        "it.cel.sets.p2",
        "it.mlt.main.p2",
        "it.net.bbnd.p2",
        "it.net.secr.p6",
        "it.net.user.p2",
        "lp.exp.durs.md",
        "lp.imp.durs.md",
        "lp.lpi.ovrl.xq",
        "ms.mil.xpnd.gd.zs",
        "ms.mil.xpnd.zs",
        "ne.exp.gnfs.zs",
        "ne.gdi.totl.zs",
        "ne.imp.gnfs.zs",
        "nv.agr.totl.zs",
        "nv.ind.totl.zs",
        "nv.srv.tetc.zs",
        "ny.adj.svng.gn.zs",
        "ny.gdp.defl.kd.zg",
        "ny.gdp.mktp.cd",
        "ny.gdp.mktp.kd.zg",
        "ny.gdp.pcap.cd",
        "ny.gdp.pcap.kd.zg",
        "ny.gdp.pcap.pp.cd",
        "ny.gdp.totl.rt.zs",
        "ny.gnp.atls.cd",
        "ny.gnp.mktp.pp.cd",
        "ny.gnp.pcap.cd",
        "ny.gnp.pcap.pp.cd",
        "ny.gns.ictr.zs",
        "pa.nus.fcrf",
        "pa.nus.ppp",
        "pa.nus.pppc.rf",
        "se.adt.1524.lt.fe.zs",
        "se.adt.1524.lt.ma.zs",
        "se.adt.1524.lt.zs",
        "se.adt.litr.fe.zs",
        "se.adt.litr.ma.zs",
        "se.adt.litr.zs",
        "se.enr.prim.fm.zs",
        "se.enr.prsc.fm.zs",
        "se.pre.enrr",
        "se.prm.cmpt.fe.zs",
        "se.prm.cmpt.ma.zs",
        "se.prm.cmpt.zs",
        "se.prm.enrl.tc.zs",
        "se.prm.enrr",
        "se.prm.gint.fe.zs",
        "se.prm.gint.ma.zs",
        "se.prm.nenr",
        "se.prm.prsl.fe.zs",
        "se.prm.prsl.ma.zs",
        "se.prm.rept.fe.zs",
        "se.prm.rept.ma.zs",
        "se.prm.tcaq.zs",
        "se.prm.uner.fe",
        "se.prm.uner.ma",
        "se.sec.enrr",
        "se.sec.nenr",
        "se.sec.prog.fe.zs",
        "se.sec.prog.ma.zs",
        "se.ter.enrr",
        "se.xpd.prim.pc.zs",
        "se.xpd.seco.pc.zs",
        "se.xpd.tert.pc.zs",
        "se.xpd.totl.gb.zs",
        "se.xpd.totl.gd.zs",
        "sg.gen.lsom.zs",
        "sg.gen.parl.zs",
        "sg.nod.cons",
        "sh.anm.chld.zs",
        "sh.dth.comm.zs",
        "sh.dth.injr.zs",
        "sh.dth.ncom.zs",
        "sh.dyn.aids.zs",
        "sh.dyn.mort",
        "sh.dyn.nmrt",
        "sh.h2o.safe.ru.zs",
        "sh.h2o.safe.ur.zs",
        "sh.h2o.safe.zs",
        "sh.hiv.1524.fe.zs",
        "sh.hiv.1524.ma.zs",
        "sh.imm.idpt",
        "sh.imm.meas",
        "sh.med.beds.zs",
        "sh.med.saop.p5",
        "sh.sgr.crsk.zs",
        "sh.sgr.irsk.zs",
        "sh.sgr.proc.p5",
        "sh.sta.acsn",
        "sh.sta.acsn.ru",
        "sh.sta.acsn.ur",
        "sh.sta.anvc.zs",
        "sh.sta.brtc.zs",
        "sh.sta.diab.zs",
        "sh.sta.maln.zs",
        "sh.sta.mmrt",
        "sh.sta.owgh.zs",
        "sh.sta.stnt.zs",
        "sh.sta.traf.p5",
        "sh.sta.wast.zs",
        "sh.svr.wast.zs",
        "sh.tbs.incd",
        "sh.xpd.oopc.to.zs",
        "sh.xpd.pcap",
        "sh.xpd.publ",
        "sh.xpd.totl.zs",
        "si.dst.02nd.20",
        "si.dst.03rd.20",
        "si.dst.04th.20",
        "si.dst.05th.20",
        "si.dst.10th.10",
        "si.dst.frst.10",
        "si.dst.frst.20",
        "si.pov.2day",
        "si.pov.dday",
        "si.pov.gap2",
        "si.pov.gaps",
        "si.pov.gini",
        "si.pov.nagp",
        "si.pov.nahc",
        "si.pov.rugp",
        "si.pov.ruhc",
        "si.pov.urgp",
        "si.pov.urhc",
        "si.spr.pc40",
        "si.spr.pc40.zg",
        "si.spr.pcap",
        "si.spr.pcap.zg",
        "sl.agr.empl.fe.zs",
        "sl.agr.empl.ma.zs",
        "sl.emp.insv.fe.zs",
        "sl.emp.totl.sp.zs",
        "sl.emp.vuln.fe.zs",
        "sl.emp.vuln.ma.zs",
        "sl.emp.work.fe.zs",
        "sl.emp.work.ma.zs",
        "sl.fam.work.fe.zs",
        "sl.fam.work.ma.zs",
        "sl.gdp.pcap.em.kd",
        "sl.ind.empl.fe.zs",
        "sl.ind.empl.ma.zs",
        "sl.srv.empl.fe.zs",
        "sl.srv.empl.ma.zs",
        "sl.tlf.0714.fe.zs",
        "sl.tlf.0714.ma.zs",
        "sl.tlf.0714.zs",
        "sl.tlf.cact.fe.zs",
        "sl.tlf.cact.ma.zs",
        "sl.tlf.totl.fe.zs",
        "sl.tlf.totl.in",
        "sl.uem.1524.fe.zs",
        "sl.uem.1524.ma.zs",
        "sl.uem.ltrm.fe.zs",
        "sl.uem.ltrm.ma.zs",
        "sl.uem.totl.fe.zs",
        "sl.uem.totl.ma.zs",
        "sl.uem.totl.zs",
        "sm.pop.netm",
        "sm.pop.refg",
        "sm.pop.refg.or",
        "sm.pop.totl",
        "sn.itk.defc.zs",
        "sp.ado.tfrt",
        "sp.dyn.cbrt.in",
        "sp.dyn.cdrt.in",
        "sp.dyn.conu.zs",
        "sp.dyn.imrt.in",
        "sp.dyn.le00.fe.in",
        "sp.dyn.le00.in",
        "sp.dyn.le00.ma.in",
        "sp.dyn.tfrt.in",
        "sp.mtr.1519.zs",
        "sp.pop.0014.to.zs",
        "sp.pop.1564.to.zs",
        "sp.pop.65up.to.zs",
        "sp.pop.dpnd",
        "sp.pop.grow",
        "sp.pop.scie.rd.p6",
        "sp.pop.tech.rd.p6",
        "sp.pop.totl",
        "sp.pop.totl.fe.zs",
        "sp.reg.brth.zs",
        "sp.reg.dths.zs",
        "sp.rur.totl",
        "sp.rur.totl.zs",
        "sp.urb.totl",
        "sp.urb.totl.in.zs",
        "sp.uwt.tfrt",
        "st.int.rcpt.xp.zs",
        "st.int.xpnd.mp.zs",
        "tg.val.totl.gd.zs",
        "tm.val.mrch.cd.wt",
        "tt.pri.mrch.xd.wd",
        "tx.val.fuel.zs.un",
        "tx.val.mmtl.zs.un",
        "tx.val.mrch.cd.wt",
        "tx.val.tech.cd",
        "tx.val.tech.mf.zs",
        "vc.ihr.psrc.p5",
        "wp_time_01.2",
        "wp_time_01.3",
    ])
