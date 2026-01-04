
import sys
import os
import structlog

# Add project root
sys.path.append(os.getcwd())

from core.portfolio.monitor import DailyMonitor

logger = structlog.get_logger()

def main():
    print("🛡️  Iniciando Monitoramento Diário de Carteira (Stop Loss & Riscos)...")
    
    monitor = DailyMonitor()
    alerts = monitor.run_check()
    
    if not alerts:
        print("⚠️  Não foi possível executar o monitoramento (sem snapshot ou sem dados atuais).")
        sys.exit(1)
        
    summary = alerts.get("summary", {})
    stop_losses = alerts.get("stop_loss", [])
    red_flags = alerts.get("red_flags", [])
    
    print(f"\n📊 Resumo da Execução:")
    print(f"   - Data do Snapshot Base: {summary.get('snapshot_date')}")
    print(f"   - Ativos Monitorados: {summary.get('checked_assets')}")
    print(f"   - Stop Losses Acionados: {len(stop_losses)}")
    print(f"   - Novos Alertas de Risco: {len(red_flags)}")
    
    # Report Stop Losses
    if stop_losses:
        print("\n🚨 ATENÇÃO: STOP LOSS ATINGIDO (-10%) 🚨")
        print("-" * 60)
        print(f"{'ATIVO':<10} {'ENTRADA':>12} {'ATUAL':>12} {'VARIAÇÃO':>10}")
        print("-" * 60)
        for alarm in stop_losses:
            print(f"{alarm['ticker']:<10} "
                  f"R$ {alarm['entry_price']:>9.2f} "
                  f"R$ {alarm['current_price']:>9.2f} "
                  f"{alarm['pnl_pct']:>9.2f}%")
        print("-" * 60)
        print("Recomendação: Venda Imediata para proteção de capital.")

    # Report New Red Flags
    if red_flags:
        print("\n⚠️  NOVOS RISCOS DETECTADOS (RED FLAGS) ⚠️")
        for alarm in red_flags:
            print(f"   - {alarm['ticker']}: {', '.join(alarm['new_flags'])}")
            
    if not stop_losses and not red_flags:
        print("\n✅ Tudo certo! Nenhum alerta crítico hoje.")

if __name__ == "__main__":
    main()
