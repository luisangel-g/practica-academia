from odoo import _, fields, models, api, exceptions

class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    company_type = fields.Selection(selection_add=[('is_school', 'Escuela'),('student_id', 'Estudiante')])
    student_id = fields.Many2one('academia.student','Estudiante')

class academia_student(models.Model):
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _name = "academia.student"
    _description = "Modelo para formación de estudiantes"
    
    @api.model
    def _get_school_default(self):
        school_id = self.env['res.partner'].search([('name', '=', 'Escuela comodin')])
        return school_id

    name = fields.Char('Nombre', size=128, required=True, track_visibility='onchange')
    last_name = fields.Char('Apellido', size=128, copy=False)
    photo = fields.Binary('Fotografia')
    create_date = fields.Datetime('Fecha de creación', readonly=True)
    note = fields.Html('Comentarios')
    active = fields.Boolean('Activo')
    curp = fields.Char('curp', size=18, copy=False)
    age = fields.Integer('Edad')
    state = fields.Selection([
        ('draf', 'Documento borrador'),
        ('prodcess', 'Proceso'),
        ('done', 'Egresado')],'Estado')
    
    ## relacionales
    partner_id = fields.Many2one('res.partner', 'Escuela', default=_get_school_default)
    country = fields.Many2one('res.country', 'Pais', related="partner_id.country_id")

    #invoice_ids = fields.Many2many('account.invoice', 'student_invoice_rel', 'student_id', 'invoice_id', 'Facturas')

    calificaciones_id = fields.One2many(
        'academia.calificacion',
        'student_id',
        'Calificaciones'
    )
    @api.constrains('curp')
    def _check_curp(self):
        if len(self.curp) != 18:
            raise exceptions.ValidationError('La curp debe ser 18 digitos')
            
    #@api.model
    #def write(self, values):
    #    if 'curp' in values:
    #        values.update({
    #            'curp': values['curp'].upper()
    #        })
    #        return super(academia_student, self).write(values)
    #        
   
    @api.model
    def create(self, values):
        if values['name']:
            nombre = values['name']
            if self.env['academia.student'].search([('name', '=', self.name)]):
                values.update({
                    'name': values['name']+"(copy)"
                })
        res = super(academia_student, self).create(values)
        partner_obj = self.env['res.partner']
        vals_to_partner = {
            'name': res['name']+" "+res['last_name'],
            'company_type': "student_id",
        }
        print(vals_to_partner)
        partner = partner_obj.create(vals_to_partner)
        print('==> partner_id: ', partner)
        return res
    
    def unlink(self):
        partner_obj = self.env['res.partner']
        partners = partner_obj.search([('student', 'in', self.ids)])
        print("partners: ", partners)
        if partners:
            for partner in partners:
                partner.unlink()
        res = super(academia_student, self).unlink()
        return res
    _order = "name"
    _defaults = {
        "state": "draft",
        "active": True
    }
