# Phase 12 NORMAL SDI export failure

## Verified evidence

Both original files and their backup copies were verified before inspecting either artifact.

| File | SHA-256 |
|---|---|
| execution.log | 3bf38d23c0ae2c89317f9dbe86a19d0641f9f5f56e714c532acb4a4aac614fd9 |
| center_raw.mat | 7e7a769cf147c8326b23d1b67d9d30d9974fd3c034f5bc6e5781ad034e3a9af3 |

The MATLAB R2026b Update 1 native stack reports std::terminate() in jetstream_export.dll, including sdi::Export::getStructuredRunData and sdi::Export::prepareStructuredData, with simulation_data_repository.dll transaction functions. The old runner called save on the whole SimulationOutput immediately after sim returned, before validating the recorded stop status. The partial 815,232-byte HDF5 MAT file contains hash and two internal signal-stream records, with no saved out object. The attempt reached serialization. The logs cannot certify its recorded simulation completion, identify the failing dataset, or establish a vendor defect beyond the observed crash site. No partial stream was interpreted as a sensor history.

## Fresh retry

The retry root contains byte-checked copies of only the approved inputs. The earlier case, its saved model, its crash outputs, and both backups are preserved. The retry verifies the approved model hash and native solver configuration, disables only Simulink signal, state and root output dataset logging in memory, and leaves To Workspace and full Simscape logging enabled. It avoids saving SimulationOutput, Dataset, or Simscape logging objects. [MathWorks Signal Logging](https://www.mathworks.com/help/simulink/gui/signallogging.html)

The new runner saves execution metadata and a plain numeric checkpoint for the 13 sensor timeseries before reading physical histories. It records all required native histories, including both reservoir commands, native pressure controls, six signed boundary rates, eight storage density/pressure/temperature histories, and the engineered outlet area, pressures and rates. The physical histories must be finite and on the native sensor clock. MATLAB dataset state histories are replaced by time-zero samples of the logged physical states for this retry. The inlet and outlet response assertions still gate completion.

It writes stages.log before and after sim, before extraction and after the numeric save. It keeps scientific output, solver diagnostics, logging overrides, and outlet evidence separate. A crash or a failed gate must be investigated from the files already written. Create another fresh root rather than reusing a case folder.

In a fresh authorized interactive MATLAB session with Center_phase12 closed, run only the NORMAL retry first.

    addpath('C:/Users/ahmd1/Documents/H2-PRISM/tools/simulation');
    rehash;
    pair = 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_sdi_retry_01';
    h2prism_center_outlet_case('execute',fullfile(pair,'normal'));

A successful retry must print PHASE 12 CAPTURE COMPLETED and produce center_raw.mat, center_extracted.mat, outlet_evidence.mat, execution.log, logging_policy.mat, and stages.log. No retry execution is claimed here.
