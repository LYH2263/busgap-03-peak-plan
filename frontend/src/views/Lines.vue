<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'

const rows = ref<any[]>([])
const editingId = ref<number | null>(null)
const form = ref({ start: '07:00', end: '09:00', headway: 5 })
const error = ref('')

async function load() { rows.value = await api('/lines') }
onMounted(load)

function hasPeak(r: any) {
  return r.peak_start_min != null && r.peak_end_min != null && r.peak_headway_min != null
}
function fmtMin(m: number) {
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`
}
function fmtWindow(r: any) {
  return hasPeak(r) ? `${fmtMin(r.peak_start_min)} – ${fmtMin(r.peak_end_min)}` : '未配置'
}
function toMin(t: string) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}
function startEdit(r: any) {
  error.value = ''
  editingId.value = r.id
  form.value = hasPeak(r)
    ? { start: fmtMin(r.peak_start_min), end: fmtMin(r.peak_end_min), headway: r.peak_headway_min }
    : { start: '07:00', end: '09:00', headway: 5 }
}
function errText(e: any) {
  try { return JSON.parse(e.message).detail ?? e.message } catch { return e.message }
}
async function save(id: number) {
  error.value = ''
  try {
    await api(`/lines/${id}/peak`, {
      method: 'PUT',
      body: JSON.stringify({
        peak_start_min: toMin(form.value.start),
        peak_end_min: toMin(form.value.end),
        peak_headway_min: Number(form.value.headway),
      }),
    })
    editingId.value = null
    await load()
  } catch (e: any) { error.value = errText(e) }
}
async function clearPeak(id: number) {
  error.value = ''
  try {
    await api(`/lines/${id}/peak`, { method: 'PUT', body: JSON.stringify({}) })
    editingId.value = null
    await load()
  } catch (e: any) { error.value = errText(e) }
}
</script>
<template>
  <h1>线路</h1>
  <p class="sub">运营线路与串车 / 大间隔判定阈值 · 两班都落在高峰窗内时按高峰计划间隔对照</p>
  <div class="card">
    <table>
      <thead><tr><th>编码</th><th>名称</th><th>计划间隔(分)</th><th>串车阈值</th><th>大间隔阈值</th><th>高峰窗</th><th>高峰间隔(分)</th><th></th></tr></thead>
      <tbody>
        <template v-for="r in rows" :key="r.id ?? JSON.stringify(r)">
          <tr>
            <td>{{ r.code }}</td><td>{{ r.name }}</td><td>{{ r.planned_headway_min }}</td>
            <td>{{ r.bunch_threshold }}</td><td>{{ r.large_threshold }}</td>
            <td>{{ fmtWindow(r) }}</td>
            <td>{{ hasPeak(r) ? r.peak_headway_min : '—' }}</td>
            <td><button class="btn" @click="startEdit(r)">设置高峰</button></td>
          </tr>
          <tr v-if="editingId === r.id">
            <td colspan="8">
              <div class="peak-edit">
                <label>高峰窗 <input type="time" v-model="form.start"> – <input type="time" v-model="form.end"></label>
                <label>高峰间隔(分) <input type="number" min="0.5" step="0.5" v-model.number="form.headway"></label>
                <button class="btn" @click="save(r.id)">保存</button>
                <button v-if="hasPeak(r)" class="btn btn-ghost" @click="clearPeak(r.id)">清除高峰配置</button>
                <button class="btn btn-ghost" @click="editingId = null">取消</button>
                <span v-if="error" class="peak-error">{{ error }}</span>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
<style scoped>
.peak-edit { display: flex; flex-wrap: wrap; align-items: center; gap: 0.6rem; font-size: 0.85rem; }
.peak-edit input {
  background: var(--bg-ink); color: var(--bg-text);
  border: 1px solid var(--bg-edge); padding: 0.3rem 0.45rem; font-size: 0.85rem;
}
.peak-edit input[type="number"] { width: 5rem; }
.btn-ghost { background: transparent; color: var(--bg-cyan); border: 1px solid var(--bg-edge); }
.peak-error { color: var(--bg-red); font-size: 0.8rem; }
</style>
