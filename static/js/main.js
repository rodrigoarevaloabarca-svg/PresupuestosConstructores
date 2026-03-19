/* Constructor Express — JavaScript global */

// Formateo de números en pesos chilenos
function formatCLP(number) {
  return '$' + Math.round(number).toLocaleString('es-CL').replace(/,/g, '.');
}

// Auto-cerrar mensajes de alerta después de 5 segundos
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('[data-auto-dismiss]');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(function () { alert.remove(); }, 500);
    }, 5000);
  });
});

// Confirmar antes de eliminar (por si se usan formularios sin modal)
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });
});
