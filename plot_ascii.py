from obspy.core import read
import os

script_path = os.path.dirname(os.path.realpath(__file__))

st = read("/home/sysop/Code/Acceleration_mseed/temp/2025/GO/ies2025erlx_2025-03-08T11:28:26.000000Z_3.9422/AZNN/2025-03-08T11:28:58.250000Z_3.9422_GO_AZNN_HNE.ascii")
print(st)
st.plot()