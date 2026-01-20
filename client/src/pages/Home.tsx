import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, Send, AlertTriangle, Clock, BarChart3 } from "lucide-react";

export default function Home() {
  const stats = [
    {
      title: "Total de E-mails",
      value: "1,284",
      description: "+12% em relação ao mês passado",
      icon: Mail,
      color: "text-blue-600",
    },
    {
      title: "Enviados com Sucesso",
      value: "1,240",
      description: "96.5% de taxa de entrega",
      icon: Send,
      color: "text-green-600",
    },
    {
      title: "Falhas de Envio",
      value: "12",
      description: "Requer atenção imediata",
      icon: AlertTriangle,
      color: "text-red-600",
    },
    {
      title: "Na Fila (Pending)",
      value: "32",
      description: "Processando via Bull Queue",
      icon: Clock,
      color: "text-amber-600",
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Visão geral da sua infraestrutura de mensageria PostmanGPX.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Atividade de Envio (24h)
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[300px] flex items-center justify-center border-t border-dashed mt-4">
              <span className="text-muted-foreground italic">
                Gráfico de atividade em tempo real em desenvolvimento...
              </span>
            </CardContent>
          </Card>

          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>Últimos E-mails</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold">
                      {String.fromCharCode(64 + i)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">contato{i}@empresa.com</p>
                      <p className="text-xs text-muted-foreground">Enviado há {i * 5} min</p>
                    </div>
                    <div className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded">
                      Sent
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

