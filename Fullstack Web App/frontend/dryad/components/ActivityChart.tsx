"use client";

import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

type ActivityChartProps = {
  data : {day : string, count : number}[];
}

export default function ActivityChart(props : ActivityChartProps) {
  const cleanedData = props.data.map((dataPoint)=>{
    const day = new Date(dataPoint.day).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
    })
    return {
      day : day,
      count : dataPoint.count
    }
  })

  return (
    <div className="card bg-base-200 rounded-2xl border border-white/8">
      <div className="card-body">
        <h2 className="card-title">Incident Activity (Last 7 days)</h2>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={cleanedData}>
              <defs>
                <linearGradient id="countGlow" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0%"
                    stopColor="#4ADE80"
                    stopOpacity={0.35}
                  />
                  <stop
                    offset="100%"
                    stopColor="#4ADE80"
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />

              <XAxis dataKey="day" dy={10} />

              <YAxis allowDecimals={false} />

              <Tooltip />

              <Area
                type="monotone"
                dataKey="count"
                stroke="#4ADE80"
                strokeWidth={3}
                fill="url(#countGlow)"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
