"""Prepare and qualify a controlled pressure-command timing pilot."""
import argparse
from pathlib import Path
from uuid import uuid4

from .final_research import SOURCE, pressure_rival_source
from .phase11 import read_json, write_json
from .phase12 import CASES, approve, prepare, specification
from .phase12_acceptance import audit, verify_pair


def design():
    trace = pressure_rival_source(SOURCE)
    if trace["source_sid"] != "55" or trace["command_sid"] != "59":
        raise ValueError("pinned command path differs")
    if trace["saved_parameters"] != {
        "step_time":"25", "step_time_unit":"s", "initial_value":"3", "initial_value_unit":"MPa",
        "final_value":"6.4", "final_value_unit":"MPa",
    }:
        raise ValueError("pinned pressure step schedule or units differ")
    spec = specification()
    spec["area"]["intervention_final"] = spec["area"]["normal_final"]
    spec["overlay"] = {"role":"internal_pressure","receiver_sid":"55","producer_sid":"59",
                       "port":"P","receiver_log":"Pressure_Source_G3/P","step_time":"1000",
                       "normal_final":"0","intervention_final":"0","unit":"MPa",
                       "min_pa":3e6-1e-6,"max_pa":6.4e6+1e-6}
    spec["step_delay"] = {"control_s":"25","intervention_s":"26"}
    spec["mechanism"] = "One-second shift of native command issuance to SID 55, not actuator lag or compressor fault."
    spec["matching"] = "Same outlet plateau, initial-state policy, boundaries, gas and solver. Only SID 59 step_time differs."
    spec["archived_anomalous_status"] = "BLOCKED"
    spec["qualification"] = ["Verify identical outlet area and pressure plateaus.",
                             "Observe both the emitted PS Step and received SID 55 pressure command.",
                             "Report numerical balance and physical sensor response on the original clock."]
    return spec


def prepare_pilot(root):
    spec = design()
    prepare(root, SOURCE, spec)
    write_json(root/"generation.json",{
        "root_id":str(uuid4()),"partition":"development",
        "parent_checkpoint":None,"random_seed":None,
        "initialization":"native model initialization for each twin; no imported checkpoint",
        "independent_family_verified":False,
        "source_sha256":spec["source_sha256"],
        "solver":spec["solver"],"outlet":spec["area"],
        "boundary_policy":"preserve native Center reservoir histories",
        "cases":{"normal":"nominal command onset", "outlet_opening":"command issued one second later; no opening"},
    })


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["prepare","approve","validate"])
    p.add_argument("root",type=Path)
    p.add_argument("--reference",type=Path)
    p.add_argument("--case",choices=CASES)
    a = p.parse_args()
    if a.action == "prepare":
        prepare_pilot(a.root)
    else:
        provenance = read_json(a.root/"generation.json")
        spec = design()
        if (provenance["partition"]!="development" or provenance["independent_family_verified"]
                or provenance["parent_checkpoint"] is not None or provenance["source_sha256"]!=spec["source_sha256"]):
            raise ValueError("unexpected pilot provenance")
        if a.action == "approve":
            if (a.root/"approval.json").exists():
                raise FileExistsError(a.root/"approval.json")
            approve(a.root,spec)
            verify_pair(a.root,None,spec)
        else:
            if a.reference is None or a.case is None:
                p.error("validate requires --reference and --case")
            receipt = audit(a.root,None,a.reference,a.case,spec)
            write_json(a.root/a.case/"command_timing_acceptance.json",receipt)


if __name__ == "__main__":
    main()
