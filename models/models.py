from odoo import _, fields, models

class res_partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    company_type = fields.Selection(selection_add=[('is_school', 'Escuela')])
class academia_student(models.Model):
    _name = "academia_student"
    _description = "Modelo para formación de estudiantes"
    
    name = fields.Char('Nombre', size=128, required=True)
    last_name = fields.Char('Apellido', size=128)
    photo = fields.Binary('Fotografia')
    create_date = fields.Datetime('Fecha de creación', readonly=True)
    note = fields.Html('Comentarios')
    active = fields.Boolean('Inactivo')
    state = fields.Selection([
        ('draf', 'Documento borrador'),
        ('prodcess', 'Proceso'),
        ('done', 'Egresado')],'Estado')
    
    ## relacionales
    partner_id = fields.Many2one('res.partner', 'Escuela')
    calificaciones_id = fields.One2many(
        'academia_calificacion',
        'student_id',
        'Calificaciones'
    )
    
    age = fields.Integer('Edad')
    _order = "name"
    _defaults = {
        "state": "draft",
        "active": True
    }
